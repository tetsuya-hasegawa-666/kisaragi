import documentSeed from "../data/documents.json";
import "./styles.css";

import { StaticDocumentRepository } from "./document-workspace/model/StaticDocumentRepository";
import { loadDashboardBootstrap } from "./shared-core/bootstrap/loadDashboardBootstrap";
import { DashboardController } from "./shared-core/controller/DashboardController";

const rootElement = document.querySelector<HTMLDivElement>("#app");

if (!rootElement) {
  throw new Error("Application root '#app' was not found.");
}

const bootstrap = await loadDashboardBootstrap(documentSeed);
const documentRepository = new StaticDocumentRepository(
  bootstrap.profiles.flatMap((profile) => profile.documents),
  {
    sourcePolicy: bootstrap.profiles.map((profile) => profile.sourcePolicy).join(" / "),
    readOnly: true
  }
);

const controller = new DashboardController(rootElement, documentRepository);

controller.start();
