import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import PublicLayout from "@/layouts/PublicLayout";
import AdminLayout from "@/layouts/AdminLayout";
import Home from "@/pages/Home";
import Product from "@/pages/Product";
import HowItWorks from "@/pages/HowItWorks";
import About from "@/pages/About";
import Contact from "@/pages/Contact";
import BlogIndex from "@/pages/BlogIndex";
import BlogPost from "@/pages/BlogPost";
import Privacy from "@/pages/Privacy";
import Terms from "@/pages/Terms";
import NotFound from "@/pages/NotFound";
import Login from "@/pages/admin/Login";
import Dashboard from "@/pages/admin/Dashboard";
import PostList from "@/pages/admin/PostList";
import PostEditor from "@/pages/admin/PostEditor";
import DemoInbox from "@/pages/admin/DemoInbox";
import Users from "@/pages/admin/Users";
import Profile from "@/pages/admin/Profile";
import Settings from "@/pages/admin/Settings";
import AnalyticsLayout from "@/pages/admin/analytics/AnalyticsLayout";
import AnalyticsOverview from "@/pages/admin/analytics/Overview";
import AnalyticsCampaigns from "@/pages/admin/analytics/Campaigns";
import CampaignEditor from "@/pages/admin/analytics/CampaignEditor";
import CampaignDetail from "@/pages/admin/analytics/CampaignDetail";
import AnalyticsContacts from "@/pages/admin/analytics/Contacts";
import AnalyticsTrust from "@/pages/admin/analytics/Trust";
import RequireAuth from "@/components/RequireAuth";

/** React Router doesn't reset scroll position on navigation by itself — without
 * this, clicking a link mid-scroll on one page leaves the next page scrolled
 * to that same offset instead of starting at the top. */
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/product" element={<Product />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/blog" element={<BlogIndex />} />
          <Route path="/blog/:slug" element={<BlogPost />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="*" element={<NotFound />} />
        </Route>

        <Route path="/admin/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <AdminLayout />
            </RequireAuth>
          }
        >
          <Route path="/admin" element={<Dashboard />} />
          <Route path="/admin/posts" element={<PostList />} />
          <Route path="/admin/posts/new" element={<PostEditor />} />
          <Route path="/admin/posts/:id" element={<PostEditor />} />
          <Route path="/admin/demo-requests" element={<DemoInbox />} />
          <Route path="/admin/users" element={<Users />} />
          <Route path="/admin/profile" element={<Profile />} />
          <Route path="/admin/settings" element={<Settings />} />

          {/* Analytics is one sidebar entry with its own tab bar, rather than
              five more entries in a sidebar that already has five. */}
          <Route path="/admin/analytics" element={<AnalyticsLayout />}>
            <Route index element={<AnalyticsOverview />} />
            <Route path="campaigns" element={<AnalyticsCampaigns />} />
            <Route path="campaigns/new" element={<CampaignEditor />} />
            <Route path="campaigns/:id" element={<CampaignDetail />} />
            <Route path="campaigns/:id/edit" element={<CampaignEditor />} />
            <Route path="contacts" element={<AnalyticsContacts />} />
            <Route path="trust" element={<AnalyticsTrust />} />
          </Route>
        </Route>
      </Routes>
    </>
  );
}
