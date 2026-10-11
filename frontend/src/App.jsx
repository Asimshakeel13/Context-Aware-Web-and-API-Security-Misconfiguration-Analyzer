import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import NewScan from "./pages/NewScan.jsx";
import ScanDetail from "./pages/ScanDetail.jsx";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewScan />} />
        <Route path="/scans/:id" element={<ScanDetail />} />
      </Routes>
    </Layout>
  );
}
