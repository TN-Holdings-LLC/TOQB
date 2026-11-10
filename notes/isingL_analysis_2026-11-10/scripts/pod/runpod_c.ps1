# RunPod REST helper: reads the key from ~/.runpod/config.toml, never prints it.
#   runpod.ps1 create            -> creates the du2 pod, prints id / gpu / cost
#   runpod.ps1 get <id>          -> status, public IP, SSH port, cost
#   runpod.ps1 stop <id> / delete <id>
#   runpod.ps1 list
param([string]$Cmd, [string]$Id, [int]$Vcpu = 64)
$key = ((Get-Content "$HOME\.runpod\config.toml" | Select-String 'api_key') -split '"')[1]
$h = @{ Authorization = "Bearer $key" }
$base = "https://rest.runpod.io/v1"
function Show($p) {
  $ssh = $p.portMappings.'22'
  "id=$($p.id) name=$($p.name) desired=$($p.desiredStatus) gpu=$($p.machine.gpuTypeId) cost/hr=$($p.costPerHr) ip=$($p.publicIp) ssh22->$ssh image=$($p.image)"
}
try {
  switch ($Cmd) {
    "create" {
      $body = @{
        name = "kime-2026-11-03"
        imageName = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
        gpuTypeIds = @("NVIDIA H100 80GB HBM3", "NVIDIA H100 NVL", "NVIDIA H200")
        gpuTypePriority = "custom"
        gpuCount = 1
        containerDiskInGb = 20
        volumeInGb = 0
        ports = @("22/tcp")
        supportPublicIp = $true
        cloudType = "SECURE"
      } | ConvertTo-Json
      Show (Invoke-RestMethod -Uri "$base/pods" -Method Post -Headers $h -ContentType "application/json" -Body $body)
    }
    "createcpu" {
      $body = @{
        name = "vs-isingl-sim-2026-11-10"
        computeType = "CPU"
        cpuFlavorIds = @("cpu5m", "cpu3m", "cpu5g", "cpu3g", "cpu5c", "cpu3c")
        cpuFlavorPriority = "custom"
        vcpuCount = $Vcpu
        imageName = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
        containerDiskInGb = 20
        ports = @("22/tcp")
        supportPublicIp = $true
      } | ConvertTo-Json
      $p = Invoke-RestMethod -Uri "$base/pods" -Method Post -Headers $h -ContentType "application/json" -Body $body
      Show $p; "vcpu=$($p.vcpuCount) mem=$($p.memoryInGb)"
    }    "get"    { Show (Invoke-RestMethod -Uri "$base/pods/$Id" -Headers $h) }
    "list"   { @(Invoke-RestMethod -Uri "$base/pods" -Headers $h) | Where-Object { $_ } | ForEach-Object { Show $_ } }
    "stop"   { Invoke-RestMethod -Uri "$base/pods/$Id/stop" -Method Post -Headers $h | Out-Null; "stopped $Id" }
    "delete" { Invoke-RestMethod -Uri "$base/pods/$Id" -Method Delete -Headers $h | Out-Null; "deleted $Id" }
    default  { "unknown command" }
  }
} catch {
  "ERROR: " + $_.Exception.Message
  if ($_.ErrorDetails.Message) { "DETAIL: " + $_.ErrorDetails.Message }
}




