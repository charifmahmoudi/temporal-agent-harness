const {AbstractPaymentProvider,ModuleProvider,Modules}=require("@medusajs/framework/utils");
const {randomUUID}=require("crypto");
class LedgerProvider extends AbstractPaymentProvider {
 static identifier="ledger";
 async call(kind,input){if(!Number.isFinite(Number(input.amount)))throw new Error("Non-numeric provider amount");const r=await fetch("http://127.0.0.1:8877/effect",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({kind,...input,raw_amount:input.amount,amount:Number(input.amount)})});if(!r.ok)throw new Error(await r.text());await r.json();return {data:input.data};}
 async initiatePayment(input){const id=randomUUID();return {id,data:{external_id:id,authorized_amount:Number(input.amount)}};}
 async authorizePayment(input){return {data:input.data,status:"authorized"};}
 async capturePayment(input){return this.call("capture",{...input,amount:input.data.authorized_amount});}
 async refundPayment(input){return this.call("refund",input);}
 async retrievePayment(input){return {data:input.data};}
 async getPaymentStatus(){return {status:"authorized"};}
 async updatePayment(input){return {data:input.data};}
 async deletePayment(input){return {data:input.data};}
 async cancelPayment(input){return {data:input.data};}
 async getWebhookActionAndData(){return {action:"not_supported"};}
}
module.exports=ModuleProvider(Modules.PAYMENT,{services:[LedgerProvider]});
