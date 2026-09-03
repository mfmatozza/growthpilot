import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Articles from "./pages/Articles";
import Audit from "./pages/Audit";
import Geo from "./pages/Geo";
import Keywords from "./pages/Keywords";
import Overview from "./pages/Overview";
import Reddit from "./pages/Reddit";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="keywords" element={<Keywords />} />
        <Route path="articles" element={<Articles />} />
        <Route path="audit" element={<Audit />} />
        <Route path="geo" element={<Geo />} />
        <Route path="reddit" element={<Reddit />} />
      </Route>
    </Routes>
  );
}
