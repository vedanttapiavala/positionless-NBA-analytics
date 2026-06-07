import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Nav     from './components/Nav'
import Loader  from './components/Loader'
import useData from './hooks/useData'
import Home      from './pages/Home'
import Explorer  from './pages/Explorer'
import Paper     from './pages/Paper'

// This code was mostly written by Claude in accordance with our course's AI use policy

export default function App() {
  const { data, loading } = useData()

  if (loading) return <Loader />

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Nav />
        <main className="main-content">
          <Routes>
            <Route path="/"          element={<Home      data={data} />} />
            <Route path="/explorer"  element={<Explorer  data={data} />} />
            <Route path="/paper"     element={<Paper />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}