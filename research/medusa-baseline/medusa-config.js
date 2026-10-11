const {defineConfig}=require("@medusajs/framework/utils");
module.exports=defineConfig({
 admin:{disable:true},
 projectConfig:{databaseUrl:process.env.DATABASE_URL,http:{jwtSecret:"qualification-only",cookieSecret:"qualification-only"}},
 modules:[{resolve:"@medusajs/medusa/payment",options:{providers:[{resolve:require("path").resolve(__dirname,"provider"),id:"ledger"}]}}]
});
