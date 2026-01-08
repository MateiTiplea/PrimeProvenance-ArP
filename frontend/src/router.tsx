import { createBrowserRouter } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import HomePage from './pages/HomePage';
// import ArtworksPage from './pages/ArtworksPage'; // Deprecated
import ArtworkDetailPage from './pages/ArtworkDetailPage';
import SPARQLPage from './pages/SPARQLPage';
import SearchPage from './pages/SearchPage';
import AboutPage from './pages/AboutPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'artworks',
        element: <SearchPage />, // Replaced ArtworksPage with SearchPage
      },
      {
        path: 'artworks/:id',
        element: <ArtworkDetailPage />,
      },
      {
        path: 'sparql',
        element: <SPARQLPage />,
      },
      {
        path: 'search',
        element: <SearchPage />,
      },
      {
        path: 'about',
        element: <AboutPage />,
      },
    ],
  },
]);

