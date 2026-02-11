import { Scene } from './components/Review/Scene';
import { Sidebar } from './components/UI/Sidebar';

function App() {
  return (
    <div className="w-full h-full flex">
      <Sidebar />
      <div className="w-[50vw] h-screen relative bg-gray-900">
        <Scene />
      </div>
      {/* Example Panel for the "other half"? Or just empty space? User said 'floor to be 50vw'. 
          If the sidebar is fixed width, the rest is > 50vw usually. 
          I will make the Scene explicitly 50vw. 
      */}
    </div>
  );
}

export default App;
