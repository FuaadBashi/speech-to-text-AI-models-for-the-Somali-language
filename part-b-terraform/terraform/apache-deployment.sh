
yum update -y


yum install -y httpd php

# Create simple PHP application showing instance metadata
cat > /var/www/html/index.php << 'PHPEOF'
<!DOCTYPE html>
<html>
<head>
    <title>Somali ASR Infrastructure - Load Balancer Test</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .info { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 Somali ASR Infrastructure</h1>
        <div class="info">
            <h2>Instance Information</h2>
            <p><strong>Hostname:</strong> <?php echo gethostname(); ?></p>
            <p><strong>Server IP:</strong> <?php echo $_SERVER['SERVER_ADDR']; ?></p>
            <p><strong>Client IP:</strong> <?php echo $_SERVER['REMOTE_ADDR']; ?></p>
            <p><strong>Timestamp:</strong> <?php echo date('Y-m-d H:i:s'); ?></p>
            <p><strong>Load Balancer:</strong> Working ✓</p>
        </div>
        <p>This page demonstrates successful load balancing across auto-scaled instances.</p>
    </div>
</body>
</html>
PHPEOF

systemctl start httpd
systemctl enable httpd


firewall-cmd --permanent --add-service=http
firewall-cmd --reload

echo "Apache deployment complete!"
