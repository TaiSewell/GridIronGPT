import {useState} from "react";

export default function App(){
  const [messages,setMessages]=useState([]);
  const [input,setInput]=useState("");

  async function ping(){
    const r = await fetch("http://localhost:8000/health");
    const data = await r.json();
    setMessages(m=>[...m,{role:"assistant",content:JSON.stringify(data)}]);
  }

  return (
    <div className="mx-auto max-w-xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Fantasy Football AI Chat</h1>
      <div className="border rounded p-3 h-[50vh] overflow-y-auto space-y-2">
        {messages.map((m,i)=>(
          <div key={i} className={m.role==="user"?"text-right":""}>
            <span className={`inline-block px-3 py-2 rounded ${m.role==="user"?"bg-gray-200":"bg-gray-100"}`}>
              {m.content}
            </span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="flex-1 border rounded px-3 py-2" value={input} onChange={e=>setInput(e.target.value)} placeholder="Type anything…" />
        <button className="px-4 py-2 rounded bg-black text-white" onClick={()=>{setMessages(m=>[...m,{role:"user",content:input}]);setInput("");}}>Send</button>
        <button className="px-3 py-2 rounded border" onClick={ping}>Ping API</button>
      </div>
    </div>
  );
}