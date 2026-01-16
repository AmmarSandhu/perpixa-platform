import { Navigate, useParams } from "react-router-dom";
import VideoDashboard from "./VideoDashboard";
import ImageDashboard from "./ImageDashboard";
import CadDashboard from "./CadDashboard";

type ToolType = "video" | "image" | "cad";

export default function DashboardShell() {
  const { tool } = useParams<{ tool: ToolType }>();

  if (!tool) {
    return <Navigate to="/dashboard/video" replace />;
  }

  switch (tool) {
    case "video":
      return <VideoDashboard />;
    case "image":
      return <ImageDashboard />;
    case "cad":
      return <CadDashboard />;
    default:
      return <Navigate to="/dashboard/video" replace />;
  }
}
