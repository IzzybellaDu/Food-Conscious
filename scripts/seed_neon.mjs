import fs from "fs";
import { Client } from "@neondatabase/serverless";

// Read .env.local
const envFile = fs.readFileSync(".env.local", "utf-8");
let dbUrl = "";
for (const line of envFile.split("\n")) {
  if (line.startsWith("DATABASE_URL_UNPOOLED=")) {
    dbUrl = line.split("=")[1].trim().replace(/^["']|["']$/g, "");
    break;
  } else if (line.startsWith("DATABASE_URL=")) {
    dbUrl = line.split("=")[1].trim().replace(/^["']|["']$/g, "");
  }
}

console.log("Connecting to Neon PostgreSQL database via Client...");
const client = new Client(dbUrl);

async function run() {
  try {
    await client.connect();
    console.log("Connected to Neon via simple query protocol!");

    const sqlContent = fs.readFileSync("seed_postgres.sql", "utf-8");
    console.log("Executing seed_postgres.sql...");

    await client.query(sqlContent);
    console.log("Successfully executed seed_postgres.sql!");

    // Verify
    const resCount = await client.query("SELECT count(*) FROM fooddata");
    console.log("Verified: fooddata row count in Neon is", resCount.rows[0].count);

    const resTables = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public'
      ORDER BY table_name
    `);
    console.log("Verified: Public tables in Neon:", resTables.rows.map(r => r.table_name).join(", "));

    const resSample = await client.query("SELECT id, name, energykj FROM fooddata LIMIT 3");
    console.log("Sample records:", resSample.rows);

    await client.end();
    console.log("All done!");
  } catch (err) {
    console.error("Error running seed_neon:", err);
    await client.end().catch(() => {});
    process.exit(1);
  }
}

run();
