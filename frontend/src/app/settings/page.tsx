import { TopBar } from "@/components/dashboard/TopBar";
import { Card } from "@/components/ui/Card";

export default function SettingsPage() {
  return (
    <>
      <TopBar title="设置" />
      <div className="flex-1 p-6 max-w-2xl space-y-5">
        <Card title="账号配置">
          <div className="space-y-4 text-sm text-[#8b949e]">
            <p>在 <code className="text-[#58a6ff] bg-[#1c2330] px-1 rounded">.env</code> 文件中配置以下参数：</p>
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#30363d]">
                  <th className="text-left pb-2 text-[#e6edf3] font-medium">变量</th>
                  <th className="text-left pb-2 text-[#e6edf3] font-medium">说明</th>
                </tr>
              </thead>
              <tbody className="space-y-2">
                {[
                  ["NEXT_PUBLIC_API_URL", "后端 FastAPI 地址（默认 http://localhost:8000）"],
                  ["BRIDGE_PROVIDER", "mock（测试）或 metaapi（真实账号）"],
                  ["METAAPI_TOKEN", "MetaApi 凭证（接入真实 MT4/MT5 时填写）"],
                ].map(([k, v]) => (
                  <tr key={k} className="border-b border-[#30363d]/50">
                    <td className="py-2 pr-4">
                      <code className="text-[#58a6ff]">{k}</code>
                    </td>
                    <td className="py-2 text-[#8b949e]">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="接入真实 MT4/MT5">
          <ol className="text-sm text-[#8b949e] space-y-2 list-decimal list-inside">
            <li>在后端 <code className="text-[#58a6ff]">requirements.txt</code> 取消 <code className="text-[#58a6ff]">metaapi-cloud-sdk</code> 注释并安装。</li>
            <li>设置 <code className="text-[#58a6ff]">BRIDGE_PROVIDER=metaapi</code> 和 <code className="text-[#58a6ff]">METAAPI_TOKEN</code>。</li>
            <li>在 MetaApi 控制台添加 MT4/MT5 账号，获取 account_id。</li>
            <li>更新本页面（或代码中）的 <code className="text-[#58a6ff]">ACCOUNT_ID</code> 常量。</li>
            <li>EA 启停功能需配合自建桥接 EA 的指令通道，详见设计文档。</li>
          </ol>
        </Card>
      </div>
    </>
  );
}
