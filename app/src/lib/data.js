// Listing-level data: one parquet file per city, queried in the browser with DuckDB-WASM.
import * as duckdb from '@duckdb/duckdb-wasm';
import wasmMvp from '@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url';
import workerMvp from '@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url';
import wasmEh from '@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url';
import workerEh from '@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url';

let connection;
const loaded = new Map();

async function connect() {
  const bundle = await duckdb.selectBundle({
    mvp: { mainModule: wasmMvp, mainWorker: workerMvp },
    eh: { mainModule: wasmEh, mainWorker: workerEh },
  });
  const db = new duckdb.AsyncDuckDB(new duckdb.VoidLogger(), new Worker(bundle.mainWorker));
  await db.instantiate(bundle.mainModule);
  return { db, conn: await db.connect() };
}

export const loadCities = () => fetch('data/cities.json').then((r) => r.json());

// Loads a city's listings into a DuckDB table named after its slug; returns the columns the map draws.
export function loadPoints(slug) {
  if (!loaded.has(slug)) loaded.set(slug, load(slug));
  return loaded.get(slug);
}

async function load(slug) {
  connection ??= connect();
  const { db, conn } = await connection;
  const file = await fetch(`data/points/${slug}.parquet`).then((r) => r.arrayBuffer());
  await db.registerFileBuffer(`${slug}.parquet`, new Uint8Array(file));
  await conn.query(`CREATE TABLE "${slug}" AS SELECT * FROM '${slug}.parquet'`);
  const t = await conn.query(`SELECT longitude, latitude, number_of_reviews, superhost, price FROM "${slug}"`);
  const column = (name) => t.getChild(name).toArray();
  const lon = column('longitude'), lat = column('latitude');
  const positions = new Float32Array(t.numRows * 2);
  for (let i = 0; i < t.numRows; i++) { positions[2 * i] = lon[i]; positions[2 * i + 1] = lat[i]; }
  const edge = (values, q) => values.slice().sort()[Math.floor(q * (values.length - 1))];
  return {
    length: t.numRows, positions,
    reviews: column('number_of_reviews'), superhost: column('superhost'), price: column('price'),
    bounds: [[edge(lon, 0.01), edge(lat, 0.01)], [edge(lon, 0.99), edge(lat, 0.99)]],
  };
}

// The listings each explore choice shows, as a SQL condition.
const WHERE = { all: 'TRUE', never: 'number_of_reviews = 0', reviewed: 'number_of_reviews > 0', superhost: 'superhost = 1' };

export async function summary(slug, show) {
  const { conn } = await connection;
  const sql = `SELECT count(*) AS listings,
  avg((number_of_reviews = 0)::INT) AS never_reviewed,
  avg(number_of_reviews) AS mean_reviews,
  median(price) AS median_price
FROM "${slug}"
WHERE ${WHERE[show]}`;
  const row = (await conn.query(sql.replace('count(*)', 'count(*)::INT'))).get(0).toJSON();
  return { ...row, sql };
}

// Among reviewed listings: the share with a perfect 5.0 rating, by how many reviews they have.
export async function perfectRatings(slug) {
  await loadPoints(slug);
  const { conn } = await connection;
  const sql = `SELECT CASE WHEN number_of_reviews <= 2 THEN '1–2' WHEN number_of_reviews <= 5 THEN '3–5'
              WHEN number_of_reviews <= 20 THEN '6–20' WHEN number_of_reviews <= 50 THEN '21–50' ELSE 'over 50' END AS label,
  count(*) AS listings,
  avg((rating = 5)::INT) AS perfect,
  avg(rating) AS mean
FROM "${slug}"
WHERE number_of_reviews > 0 AND rating IS NOT NULL
GROUP BY label
ORDER BY min(number_of_reviews)`;
  const t = await conn.query(sql.replace('count(*)', 'count(*)::INT'));
  return { rows: t.toArray().map((r) => r.toJSON()), sql };
}
