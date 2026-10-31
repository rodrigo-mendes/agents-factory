import { createBrowserRouter } from "react-router-dom";
import axios from "axios";

export const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  { path: "/orders", element: <Orders /> },
]);

export function loadOrders() {
  return axios.get("http://localhost:3000/api/orders");
}

export function createOrder(order) {
  return axios.post("/api/orders", order);
}
