import { useEffect, useState } from 'react';

export default function Download() {
  const [downloadUrl, setDownloadUrl] = useState('');
  const [version, setVersion] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://api.github.com/repos/KezLahd/Screen-Split/releases/latest')
      .then(response => response.json())
      .then(data => {
        const asset = data.assets.find(asset => asset.name === 'ScreenSplit-Setup.exe');
        if (asset) {
          setDownloadUrl(asset.browser_download_url);
          setVersion(data.tag_name);
        }
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching release:', error);
        setLoading(false);
      });
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Download Screen Split</h1>
      {loading ? (
        <p>Loading download information...</p>
      ) : downloadUrl ? (
        <div>
          <p className="mb-4">Latest version: {version}</p>
          <a
            href={downloadUrl}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
            download
          >
            Download for Windows
          </a>
          <p className="mt-4 text-sm text-gray-600">
            By downloading, you agree to the terms of the MIT License.
          </p>
        </div>
      ) : (
        <p>No download available at this time.</p>
      )}
    </div>
  );
} 