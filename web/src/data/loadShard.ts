import { DataError, dataRoot, fetchJson } from "./loadIndex";
import { shardSchema, type Shard, type ShardImage } from "./shardSchema";

const shards = new Map<string, Promise<Shard | null>>();

async function fetchShard(url: string): Promise<Shard | null> {
  try {
    return await fetchJson(url, shardSchema);
  } catch (error) {
    // No shard means the sequence has not been analysed yet. Dev servers answer
    // unknown paths with the app's HTML page, which fails to parse as JSON.
    const missing = error instanceof DataError && error.status === 404;
    if (missing || error instanceof SyntaxError) {
      return null;
    }
    throw error;
  }
}

// One shard covers a whole sequence, so walking along it reuses the same fetch.
export function loadShard(
  country: string,
  sequenceId: string,
): Promise<Shard | null> {
  if (!/^[A-Z]{2}$/.test(country) || !/^[A-Za-z0-9_-]+$/.test(sequenceId)) {
    return Promise.resolve(null);
  }
  const url = `${dataRoot}/images/${country}/${sequenceId}.json`;
  let shard = shards.get(url);
  if (!shard) {
    shard = fetchShard(url);
    shard.catch(() => {
      shards.delete(url);
    });
    shards.set(url, shard);
  }
  return shard;
}

export function findImage(shard: Shard | null, imageId: string) {
  if (!shard) {
    return null;
  }
  const image: ShardImage | undefined = shard.images.find(
    (candidate) => candidate.id === imageId,
  );
  return image ?? null;
}

export function clearShardCache() {
  shards.clear();
}
