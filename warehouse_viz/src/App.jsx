import { Scene } from './components/Review/Scene';
import { Sidebar } from './components/UI/Sidebar';

function App() {
  return (
    <div className="w-full h-full flex">
      <Sidebar />
      <div className="flex-1 h-screen relative">
        <Scene />
      </div>
    </div>
  );
}

export default App;
