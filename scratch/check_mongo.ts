import { MongoClient } from "npm:mongodb";

const uri = "mongodb+srv://novox_interns:novox_intern26@novox-website-content-m.gjpfntc.mongodb.net";
const client = new MongoClient(uri);

try {
  await client.connect();
  const db = client.db("chat_logs_db");
  const collections = await db.listCollections().toArray();
  console.log("Collections in chat_logs_db:");
  collections.forEach(c => console.log(" - " + c.name));
  console.log(`Total: ${collections.length} collections`);
} catch (e) {
  console.error(e);
} finally {
  await client.close();
}
