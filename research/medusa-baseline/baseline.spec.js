require("reflect-metadata");
const fs=require("fs"),path=require("path"),assert=require("node:assert/strict");
const {medusaIntegrationTestRunner}=require("@medusajs/test-utils");
const {Modules,ContainerRegistrationKeys}=require("@medusajs/framework/utils");
const flows=require("@medusajs/core-flows");
const out=path.resolve(__dirname,"../../evidence");
fs.mkdirSync(out,{recursive:true});
function event(type,data){fs.appendFileSync(path.join(out,"events.jsonl"),JSON.stringify({time:new Date().toISOString(),type,data})+"\n");}
medusaIntegrationTestRunner({
 dbName:"medusa_return_qualification",
 testSuite:({getContainer,dbConfig})=>{
 it("qualifies two returned units, one damaged, and explicit refund",async()=>{
 const c=getContainer(),orderSvc=c.resolve(Modules.ORDER),inv=c.resolve(Modules.INVENTORY),pay=c.resolve(Modules.PAYMENT);
 const link=c.resolve(ContainerRegistrationKeys.LINK);
 async function run(name,input){event("workflow-start",{name,input});try{const r=await flows[name](c).run({input,throwOnError:true});event("workflow-complete",{name,result:r.result});return r.result;}catch(e){event("workflow-error",{name,error:String(e),stack:e.stack});throw e;}}
 const region=await c.resolve(Modules.REGION).createRegions({name:"Qualification",currency_code:"usd",countries:["us"]});
 const location=await c.resolve(Modules.STOCK_LOCATION).createStockLocations({name:"Qualification"});
 const product=await c.resolve(Modules.PRODUCT).createProducts({title:"Qualification",variants:[{title:"Unit",sku:"qualification",manage_inventory:true}]});
 const inventory=await inv.createInventoryItems({sku:"qualification"});
 await inv.createInventoryLevels({inventory_item_id:inventory.id,location_id:location.id,stocked_quantity:0});
 await link.create({[Modules.PRODUCT]:{variant_id:product.variants[0].id},[Modules.INVENTORY]:{inventory_item_id:inventory.id}});
 const order=await orderSvc.createOrders({region_id:region.id,currency_code:"usd",email:"qualification@example.invalid",items:[{title:"Unit",variant_id:product.variants[0].id,quantity:2,unit_price:25}]});
 const item=order.items[0];
 for(const action of ["FULFILL_ITEM","SHIP_ITEM"]){await orderSvc.addOrderAction({action,order_id:order.id,version:order.version,reference:"fulfillment",reference_id:"fixture_fulfillment",details:{reference_id:item.id,quantity:2}});}
 await orderSvc.applyPendingOrderActions(order.id);
 const collection=await pay.createPaymentCollections({currency_code:"usd",amount:50});
 await link.create({[Modules.ORDER]:{order_id:order.id},[Modules.PAYMENT]:{payment_collection_id:collection.id}});
 const session=await pay.createPaymentSession(collection.id,{provider_id:"pp_ledger_ledger",currency_code:"usd",amount:50,data:{},context:{}});
 const payment=await pay.authorizePaymentSession(session.id,{});
 await run("capturePaymentWorkflow",{payment_id:payment.id,amount:50});
 let returnId;
 async function snapshot(stage){
 const tables={};
 const observer=new (require("pg").Client)({connectionString:dbConfig.clientUrl});
 await observer.connect();
 try {
 for(const table of ["inventory_level","return","return_item","payment","capture","refund","order_transaction","order_summary"]){
  tables[table]=(await observer.query('SELECT * FROM "'+table+'"')).rows;
 }
 } finally {await observer.end();}
 const external=await (await fetch("http://127.0.0.1:8877/ledger")).json();
 const observed={stage,ids:{order:order.id,item:item.id,inventory:inventory.id,location:location.id,payment:payment.id,return:returnId},tables,external};
 fs.writeFileSync(path.join(out,stage+".json"),JSON.stringify(observed,null,2));
 event("snapshot",{stage});
 return observed;
 }
 const before=await snapshot("before-return");
 assert.equal(Number(before.tables.inventory_level[0].stocked_quantity),0);
 assert.equal(before.external.filter(x=>x.kind==="capture").length,1);
 assert.equal(Number(before.external.find(x=>x.kind==="capture").amount),50);
 const change=await run("beginReturnOrderWorkflow",{order_id:order.id,location_id:location.id});
 returnId=change.return_id;
 await run("requestItemReturnWorkflow",{return_id:returnId,items:[{id:item.id,quantity:2}]});
 await run("confirmReturnRequestWorkflow",{return_id:returnId});
 await run("beginReceiveReturnWorkflow",{return_id:returnId});
 await run("receiveItemReturnRequestWorkflow",{return_id:returnId,items:[{id:item.id,quantity:1}]});
 await run("dismissItemReturnRequestWorkflow",{return_id:returnId,items:[{id:item.id,quantity:1}]});
 await run("confirmReturnReceiveWorkflow",{return_id:returnId});
 const received=await snapshot("after-receipt");
 assert.equal(Number(received.tables.inventory_level[0].stocked_quantity),1);
 const ri=received.tables.return_item.find(x=>x.return_id===returnId);
 assert.equal(Number(ri.received_quantity),2);
 assert.equal(Number(ri.damaged_quantity),1);
 assert.equal(received.external.filter(x=>x.kind==="refund").length,0);
 await run("refundPaymentWorkflow",{payment_id:payment.id,amount:50});
 const final=await snapshot("after-refund");
 const refunds=final.external.filter(x=>x.kind==="refund");
 assert.equal(refunds.length,1); assert.equal(Number(refunds[0].amount),50);
 assert.equal(final.tables.refund.length,1);assert.equal(Number(final.tables.refund[0].amount),50);
 assert.equal(final.tables.order_transaction.filter(x=>x.reference==="refund").length,1);
 assert.equal(Number(final.tables.order_transaction.find(x=>x.reference==="refund").amount),-50);
 assert.equal(Number(final.tables.inventory_level[0].stocked_quantity),1);
 const latestVersion=Math.max(...final.tables.order_summary.map(x=>x.version));
 const latest=final.tables.order_summary.filter(x=>x.version===latestVersion);
 assert.ok(latest.length>0);
 for(const row of latest){assert.equal(Number(row.totals.refunded_total),50);assert.equal(Number(row.totals.pending_difference),0);}
 assert.equal(final.tables.capture.length,1);assert.equal(Number(final.tables.capture[0].amount),50);
 fs.writeFileSync(path.join(out,"summary.json"),JSON.stringify({status:"passed",case:"two-units-one-damaged",stock_before:0,stock_after:1,received:2,damaged:1,captured:50,refunded:50,refund_count:1,injected_faults:0,limitations:["seeded fulfillment","payment test contract","no crash/recovery experiment"]},null,2));
 });
 }});
