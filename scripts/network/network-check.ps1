# Network Diagnostic Script for Office Network Diagnostics
# Collects Wi-Fi, adapter, gateway, DNS, local & public IP information
# and verifies against QUBIQON approved public IP whitelist.

param(
    [switch]$Verbose,
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Continue"

function Write-Section($title) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Get-PublicIP {
    $urls = @(
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com"
    )
    foreach ($url in $urls) {
        try {
            $ip = (Invoke-RestMethod -Uri $url -TimeoutSec 5).Trim()
            if ($ip -match '^\d{1,3}(\.\d{1,3}){3}$') {
                return $ip
            }
        } catch {
            continue
        }
    }
    return $null
}

function Get-ApprovedIPs {
    # Prefer external config; fall back to defaults
    $defaults = @("103.142.31.212", "103.181.238.50")
    if ($ConfigPath -and (Test-Path $ConfigPath)) {
        try {
            $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
            if ($cfg.approved_public_ips) {
                return $cfg.approved_public_ips
            }
        } catch {}
    }
    # Also try relative settings.json
    $candidates = @(
        ".\settings.json",
        ".\config\settings.json",
        "$PSScriptRoot\..\..\settings.json",
        "$PSScriptRoot\..\..\config\settings.json"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            try {
                $cfg = Get-Content $c -Raw | ConvertFrom-Json
                if ($cfg.approved_public_ips) {
                    return $cfg.approved_public_ips
                }
            } catch {}
        }
    }
    return $defaults
}

Write-Host "Dynamic Script Runner – Network Diagnostics" -ForegroundColor Green
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# --- Wi-Fi Information (Windows) ---
Write-Section "Wi-Fi Information"

$wifi = $null
try {
    $wifiProfile = netsh wlan show interfaces 2>$null
    if ($wifiProfile) {
        $ssid   = ($wifiProfile | Select-String '^\s*SSID\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
        $bssid  = ($wifiProfile | Select-String '^\s*BSSID\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
        $signal = ($wifiProfile | Select-String '^\s*Signal\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
        $channel= ($wifiProfile | Select-String '^\s*Channel\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()
        $radio  = ($wifiProfile | Select-String '^\s*Radio type\s*:\s*(.+)$').Matches.Groups[1].Value.Trim()

        Write-Host "SSID            : $ssid"
        Write-Host "BSSID (AP MAC)  : $bssid"
        Write-Host "Signal Strength : $signal"
        Write-Host "Channel         : $channel"
        Write-Host "Radio Type      : $radio"
    } else {
        Write-Host "No active Wi-Fi interface detected (or netsh unavailable)."
    }
} catch {
    Write-Host "Unable to query Wi-Fi details: $_"
}

# --- Network Adapter & IP ---
Write-Section "Network Adapter & Local IP"

$adapters = Get-NetIPConfiguration -ErrorAction SilentlyContinue | Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq 'Up' }
if ($adapters) {
    foreach ($a in $adapters) {
        Write-Host "Adapter         : $($a.InterfaceAlias)"
        Write-Host "Description     : $($a.NetAdapter.InterfaceDescription)"
        Write-Host "Local IPv4      : $($a.IPv4Address.IPAddress)"
        Write-Host "Prefix Length   : $($a.IPv4Address.PrefixLength)"
        Write-Host "Default Gateway : $($a.IPv4DefaultGateway.NextHop)"
        Write-Host "DNS Servers     : $($a.DNSServer.ServerAddresses -join ', ')"
        Write-Host ""
    }
} else {
    # Fallback
    $ipconfig = ipconfig 2>$null
    Write-Host $ipconfig
}

# --- Public IP & Whitelist ---
Write-Section "Public IP & Whitelist Check"

$publicIP = Get-PublicIP
$approved = Get-ApprovedIPs

if (-not $publicIP) {
    Write-Host "Public IP       : UNKNOWN (detection failed)"
    Write-Host "Whitelist Status: UNKNOWN"
} else {
    Write-Host "Public IP       : $publicIP"
    if ($approved -contains $publicIP) {
        Write-Host "Whitelist Status: APPROVED" -ForegroundColor Green
    } else {
        Write-Host "Whitelist Status: NOT APPROVED" -ForegroundColor Yellow
        Write-Host "Approved IPs    : $($approved -join ', ')"
    }
}

# --- Available Wi-Fi Networks (brief) ---
Write-Section "Available Wi-Fi Networks (top 10)"
try {
    $networks = netsh wlan show networks mode=bssid 2>$null
    if ($networks) {
        $networks | Select-Object -First 40
    } else {
        Write-Host "Unable to list networks."
    }
} catch {
    Write-Host "netsh wlan show networks failed."
}

Write-Host ""
Write-Host "Diagnostics complete." -ForegroundColor Green
exit 0
