import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Register from './components/RegisterSimple/Register';
import Login from './components/LoginSimple/Login';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import MovieDetailsPage from './pages/MovieDetailsPage';
import FavoritesPage from './pages/FavoritesPage';
import MyRatingsPage from './pages/MyRatingsPage';
import RecommendedPage from './pages/RecommendedPage';
import './App.css';

function Layout({ children }) {
  const location = useLocation();
  
  // Não mostrar Navbar nas páginas de login e registro
  const hideNavbar = ['/login', '/register'].includes(location.pathname);

  return (
    <div className="app-layout">
      {!hideNavbar && <Navbar />}
      <main className="app-main">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <HomePage />
            </Layout>
          }
        />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/movie/:id"
          element={
            <Layout>
              <MovieDetailsPage />
            </Layout>
          }
        />
        <Route
          path="/favorites"
          element={
            <Layout>
              <FavoritesPage />
            </Layout>
          }
        />
        <Route
          path="/my-ratings"
          element={
            <Layout>
              <MyRatingsPage />
            </Layout>
          }
        />
        <Route
          path="/recommended"
          element={
            <Layout>
              <RecommendedPage />
            </Layout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
