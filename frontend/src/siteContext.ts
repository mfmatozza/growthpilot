import { useOutletContext } from "react-router-dom";

import type { Site } from "./api/types";

export interface SiteContext {
  siteId: string;
  site: Site | null;
}

export function useSiteContext(): SiteContext {
  return useOutletContext<SiteContext>();
}
