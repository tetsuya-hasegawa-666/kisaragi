export interface DocumentRecord {
  id: string;
  profileId: string;
  profileLabel: string;
  nodeKind: "file" | "directory";
  title: string;
  path: string;
  body: string;
  tags: string[];
}
