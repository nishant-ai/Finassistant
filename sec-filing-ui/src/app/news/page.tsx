'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

interface Article {
  title: string;
  description: string;
  url: string;
  urlToImage: string; // For the image
  source: { name: string };
}

function NewsPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const searchParams = useSearchParams();
  const period = searchParams.get('period') || 'week';
  const title = period === 'week' ? 'Latest Finance News (Past Week)' : 'Breaking News (Past Month)';

  useEffect(() => {
    const fetchNews = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`http://127.0.0.1:8000/news/general?period=${period}&limit=50`);
        const data = await response.json();
        setArticles(data.articles);
      } catch (error) {
        console.error("Failed to fetch news", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchNews();
  }, [period]);

  return (
    <main className="min-h-screen p-4 sm:p-8 bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
            <Link href="/" className="text-purple-400 hover:text-purple-300">&larr; Back to Home</Link>
            <h1 className="text-4xl font-bold text-center mt-2 text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500">{title}</h1>
        </div>
        {isLoading ? (
          <p className="text-center">Loading news...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {articles.map((article, index) => (
              <a key={index} href={article.url} target="_blank" rel="noopener noreferrer" className="flex flex-col bg-gray-800 rounded-lg border border-gray-700 overflow-hidden hover:border-purple-500 transition-all duration-300 transform hover:-translate-y-1">
                {article.urlToImage && <img src={article.urlToImage} alt={article.title} className="w-full h-40 object-cover" />}
                <div className="p-4 flex flex-col flex-grow">
                  <h3 className="font-bold text-lg text-gray-200 line-clamp-3">{article.title}</h3>
                  <p className="text-sm text-gray-400 mt-2 line-clamp-4 flex-grow">{article.description}</p>
                  <p className="text-xs text-purple-400 mt-4">{article.source.name}</p>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

export default function NewsPageWrapper() {
    return <Suspense><NewsPage /></Suspense>
}