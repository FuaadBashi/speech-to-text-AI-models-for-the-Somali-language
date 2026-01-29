<?php
// This is a reference copy of the application
// The actual file is deployed via user-data.sh to /var/www/html/index.php

// Get instance metadata
$hostname = gethostname();
$local_ip = $_SERVER['SERVER_ADDR'] ?? 'N/A';
$request_time = date('Y-m-d H:i:s');

// Try to get instance ID from metadata service (Huawei Cloud)
$instance_id = 'N/A';
$metadata_url = 'http://169.254.169.254/openstack/latest/meta_data.json';
$ctx = stream_context_create([
    'http' => [
        'timeout' => 2,
        'ignore_errors' => true
    ]
]);

$metadata = @file_get_contents($metadata_url, false, $ctx);
if ($metadata) {
    $data = json_decode($metadata, true);
    $instance_id = $data['uuid'] ?? $data['instance_id'] ?? 'N/A';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Somali ASR Infrastructure</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .info-grid {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 15px;
            margin: 20px 0;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        .label {
            font-weight: bold;
            color: #764ba2;
        }
        .value {
            color: #333;
            font-family: 'Courier New', monospace;
            background: white;
            padding: 5px 10px;
            border-radius: 5px;
            word-break: break-all;
        }
        .highlight {
            background: #667eea;
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.2em;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 0.9em;
        }
        .status {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Somali ASR</h1>
        <div class="subtitle">Cloud Infrastructure Demo</div>
        
        <div class="highlight">
            <strong>Server:</strong> <?php echo htmlspecialchars($hostname); ?>
            <div class="status">✓ Active</div>
        </div>
        
        <div class="info-grid">
            <div class="label">Hostname:</div>
            <div class="value"><?php echo htmlspecialchars($hostname); ?></div>
            
            <div class="label">Local IP:</div>
            <div class="value"><?php echo htmlspecialchars($local_ip); ?></div>
            
            <div class="label">Instance ID:</div>
            <div class="value"><?php echo htmlspecialchars($instance_id); ?></div>
            
            <div class="label">Request Time:</div>
            <div class="value"><?php echo htmlspecialchars($request_time); ?></div>
            
            <div class="label">Client IP:</div>
            <div class="value"><?php echo htmlspecialchars($_SERVER['REMOTE_ADDR'] ?? 'N/A'); ?></div>
        </div>
        
        <div class="footer">
            <p>Deployed via Terraform on Huawei Cloud</p>
            <p>Auto-scaling enabled | Load balanced</p>
        </div>
    </div>
</body>
</html>
