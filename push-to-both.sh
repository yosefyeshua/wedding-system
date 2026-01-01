#!/bin/bash

echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "📤 Pushing to Azure DevOps..."
git push https://GFbv9kJO5SK9JUJmui4PE47p9xUHCLA4uRnmOH0g2yGoQ08AN092JQQ399BLACAAAABJWM0AAASAZDO4b8a@dev.azure.com/rshemtov/פרויקט%20הנדסת%20תוכנה/_git/פרויקט%20הנדסת%20תוכנה main

echo ""
echo "✅ Done!"
