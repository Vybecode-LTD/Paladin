import { Routes, Route } from "react-router-dom";
import PublicLayout from "@/layouts/PublicLayout";
import AdminLayout from "@/layouts/AdminLayout";
import Home from "@/pages/Home";
import Product from "@/pages/Product";
import HowItWorks from "@/pages/HowItWorks";
import About from "@/pages/About";
import Contact from "@/pages/Contact";
import BlogIndex from "@/pages/BlogIndex";
import BlogPost from "@/pages/BlogPost";
import Login from "@/pages/admin/Login";
import Dashboard from "@/pages/admin/Dashboard";
import PostList from "@/pages/admin/PostList";
import PostEditor from "@/pages/admin/PostEditor";
import DemoInbox from "@/pages/admin/DemoInbox";
import RequireAuth from "@/components/RequireAuth";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/product" element={<Product />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/blog" element={<BlogIndex />} />
        <Route path="/blog/:slug" element={<BlogPost />} />
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
      </Route>
    </Routes>
  );
}
