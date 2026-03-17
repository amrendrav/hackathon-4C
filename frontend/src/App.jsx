import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar       from './components/Navbar';
import BriefingPage from './pages/BriefingPage';
import AgentsPage   from './pages/AgentsPage';
import DataPage     from './pages/DataPage';

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/"       element={<BriefingPage />} />
          <Route path="/agents" element={<AgentsPage />}   />
          <Route path="/data"   element={<DataPage />}     />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
