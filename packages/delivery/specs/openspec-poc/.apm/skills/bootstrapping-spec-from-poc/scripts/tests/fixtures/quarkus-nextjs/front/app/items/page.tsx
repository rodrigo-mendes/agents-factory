import { listItems } from "../../lib/api";

export default async function ItemsPage() {
  const items = await listItems();
  if (items.length === 0) {
    return <p>No items yet</p>;
  }
  return <ul>{items.map((i) => <li key={i.id}>{i.name}</li>)}</ul>;
}
