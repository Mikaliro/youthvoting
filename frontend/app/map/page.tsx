import Sidebar from "@/app/_components/Sidebar";
import MapView from "@/app/_components/MapView";

export default function MapPage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 relative">
        <MapView />
      </main>
    </div>
  );
}
