import { NavLink, useNavigate } from "react-router-dom";
import { useState } from "react";
import {
  LayoutDashboard, PlusCircle, History, Lightbulb, Building2, Database,
  GitCompare, FileText, Bell, Settings as SettingsIcon, LogOut, ChevronLeft, ChevronRight,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useBusiness } from "../context/BusinessContext";

const NAV = [
  {
    group: "MAIN",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/simulation/new", label: "New Simulation", icon: PlusCircle },
      { to: "/simulations", label: "Simulation History", icon: History },
      { to: "/insights", label: "Insights", icon: Lightbulb },
    ],
  },
  {
    group: "BUSINESS",
    items: [
      { to: "/business", label: "Business Profile", icon: Building2 },
      { to: "/business-data", label: "Business Data", icon: Database },
    ],
  },
  {
    group: "TOOLS",
    items: [
      { to: "/compare", label: "Scenario Comparison", icon: GitCompare },
      { to: "/reports", label: "Reports", icon: FileText },
    ],
  },
  {
    group: "SYSTEM",
    items: [
      { to: "/notifications", label: "Notifications", icon: Bell },
      { to: "/settings", label: "Settings", icon: SettingsIcon },
    ],
  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const { activeBusiness } = useBusiness();
  const navigate = useNavigate();

  return (
    <aside
      className={`h-screen sticky top-0 flex flex-col bg-base-900 border-r border-base-700 transition-all ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      <div className="flex items-center justify-between px-4 py-4 border-b border-base-700">
        {!collapsed && (
          <span className="font-semibold text-accent-500 tracking-tight">Decision Simulator</span>
        )}
        <button onClick={() => setCollapsed((c) => !c)} className="text-gray-500 hover:text-gray-300">
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-3">
        {NAV.map((section) => (
          <div key={section.group} className="mb-4">
            {!collapsed && (
              <div className="px-4 text-[10px] tracking-widest text-gray-600 mb-1">{section.group}</div>
            )}
            {section.items.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2 mx-2 rounded-lg text-sm transition ${
                    isActive
                      ? "bg-accent-500/10 text-accent-400 border border-accent-500/30"
                      : "text-gray-400 hover:bg-base-800 hover:text-gray-200"
                  }`
                }
              >
                <Icon size={17} />
                {!collapsed && <span>{label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="border-t border-base-700 p-4">
        {!collapsed && (
          <div className="mb-2 text-sm">
            <p className="text-gray-200 truncate">{user?.name}</p>
            <p className="text-gray-500 text-xs truncate">
              {activeBusiness ? activeBusiness.name : "No business yet"}
            </p>
          </div>
        )}
        <button
          onClick={() => {
            logout();
            navigate("/login");
          }}
          className="flex items-center gap-2 text-gray-500 hover:text-red-400 text-sm"
        >
          <LogOut size={16} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
