const { MongoClient } = require("mongodb");

const uri = "mongodb+srv://novox_interns:novox_intern26@novox-website-content-m.gjpfntc.mongodb.net";
const client = new MongoClient(uri);

async function run() {
  try {
    await client.connect();
    const db = client.db("chat_logs_db");
    
    // Explicitly create the collection
    const existing = await db.listCollections().toArray();
    if (!existing.find(c => c.name === 'chat_messages')) {
        await db.createCollection("chat_messages");
        console.log("Created new collection: chat_messages");
    }

    const collections = await db.listCollections().toArray();
    console.log("\nCollections in chat_logs_db:");
    collections.forEach(c => console.log(" - " + c.name));
    console.log(`Total: ${collections.length} collections`);
  } catch (e) {
    console.error(e);
  } finally {
    await client.close();
  }
}

run();
