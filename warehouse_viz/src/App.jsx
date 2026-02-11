import { Scene } from './components/Review/Scene';
import { Sidebar } from './components/UI/Sidebar';
import { ControlsHelp } from './components/UI/ControlsHelp';

function App() {
  return (
    <div className="w-full h-full flex">
      <Sidebar />
      <div className="flex-1 h-screen relative">
        <Scene />
      </div>
      <ControlsHelp />
    </div>
  );
}

export default App;
