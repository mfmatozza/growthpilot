import { Navigate, Outlet } from "react-router-dom";

import { isAuthed } from "../auth";

export default function RequireAuth() {
  return isAuthed() ? <Outlet /> : <Navigate to="/login" replace />;
}
