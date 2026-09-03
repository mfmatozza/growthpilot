import { defineRailway, github, postgres, project, service, volume } from "railway/iac";

export default defineRailway(() => {
  const Postgres = postgres("Postgres", { region: "ams" });
  const postgresVolume = volume("postgres-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "ams", sizeMB: 500 });

  const backend = service("backend", {
    source: github("mfmatozza/growthpilot", { rootDirectory: "backend" }),
    replicas: { "ams": 1 },
    healthcheck: "/health",
    env: {
      DATABASE_URL: Postgres.env.DATABASE_URL,
    },
  });

  const frontend = service("frontend", {
    source: github("mfmatozza/growthpilot", { rootDirectory: "frontend" }),
    replicas: { "ams": 1 },
  });

  return project("growthpilot", {
    resources: [Postgres, backend, frontend, postgresVolume],
  });
});
