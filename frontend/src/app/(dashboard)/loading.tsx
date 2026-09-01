export default function DashboardLoading() {
 return (
 <div className="flex h-64 w-full items-center justify-center rounded-xl border bg-white p-6 shadow-sm">
 <div className="flex items-center gap-2 text-sm text-slate-500">
 <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"/>
 <span>Loading content...</span>
 </div>
 </div>
 );
}
