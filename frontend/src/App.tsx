import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import Articles from "./pages/Articles";
import Audit from "./pages/Audit";
import Digest from "./pages/Digest";
import Geo from "./pages/Geo";
import Keywords from "./pages/Keywords";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import SitesHome from "./pages/SitesHome";

// Reddit.tsx is intentionally not routed — see docs/DECISIONS.md #29.
// The file stays in the repo, ready to re-wire the moment Reddit API
// access exists.

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      <Route element={<RequireAuth />}>
        <Route path="/dashboard" element={<SitesHome />} />
        <Route path="/dashboard/sites/:siteId" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="keywords" element={<Keywords />} />
          <Route path="articles" element={<Articles />} />
          <Route path="audit" element={<Audit />} />
          <Route path="geo" element={<Geo />} />
          <Route path="digest" element={<Digest />} />
        </Route>
      </Route>
    </Routes>
  );
}
