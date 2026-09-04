import { Routes, Route } from "react-router-dom";
import { BusinessProvider } from "./context/BusinessContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import NewSimulation from "./pages/NewSimulation";
import SimulationResults from "./pages/SimulationResults";
import SimulationHistory from "./pages/SimulationHistory";
import Insights from "./pages/Insights";
import BusinessProfile from "./pages/BusinessProfile";
import BusinessData from "./pages/BusinessData";
import Compare from "./pages/Compare";
import Reports from "./pages/Reports";
import Notifications from "./pages/Notifications";
import Settings from "./pages/Settings";

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <BusinessProvider>{children}</BusinessProvider>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/onboarding"
        element={
          <Protected>
            <Onboarding />
          </Protected>
        }
      />

      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/simulation/new" element={<NewSimulation />} />
        <Route path="/simulation/:id/results" element={<SimulationResults />} />
        <Route path="/simulations" element={<SimulationHistory />} />
        <Route path="/insights" element={<Insights />} />
        <Route path="/business" element={<BusinessProfile />} />
        <Route path="/business-data" element={<BusinessData />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Landing />} />
    </Routes>
  );
}
