const BASE = process.env.NEXT_PUBLIC_API_URL;

export async function listItems() {
  const res = await fetch(`${BASE}/items`);
  return res.json();
}

export async function getItem(id: string) {
  return fetch(`${BASE}/items/${id}`).then((r) => r.json());
}

export async function archiveItem(id: string) {
  return fetch(`${BASE}/items/${id}/archive`, {
    method: "POST",
  });
}
