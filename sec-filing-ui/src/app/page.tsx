// Home Page

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// --- Type Definitions ---
interface Company { name: string; ticker: string; }
interface Article { title: string; description: string; url: string; }
interface ChatHistoryItem { docId: string; companyName: string; ticker: string; }

// --- News Card Component ---
const NewsCard = ({ article }: { article: Article }) => (
  <a href={article.url} target="_blank" rel="noopener noreferrer" className="block p-4 bg-gray-700/50 rounded-lg hover:bg-purple-900/50 border border-gray-700 transition duration-200">
    <h3 className="font-bold text-purple-400 truncate">{article.title}</h3>
    <p className="text-sm text-gray-400 mt-1 line-clamp-2">{article.description}</p>
  </a>
);

export default function HomePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [weeklyNews, setWeeklyNews] = useState<Article[]>([]);
  const [monthlyNews, setMonthlyNews] = useState<Article[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [isNewsLoading, setIsNewsLoading] = useState(true); // Dedicated loading state for news
  const router = useRouter();

  useEffect(() => {
    // 1. Fetch Companies
    fetch('/companies.json')
      .then((res) => res.json())
      .then(setCompanies)
      .catch(() => setError('Could not load company data.'));

    // 2. Fetch News with dedicated loading state
    const fetchNews = async () => {
      setIsNewsLoading(true);
      try {
        const [weeklyRes, monthlyRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/news/general?period=week&limit=5'),
          fetch('http://127.0.0.1:8000/news/general?period=month&limit=5')
        ]);
        if (!weeklyRes.ok || !monthlyRes.ok) throw new Error("Failed to fetch news.");
        const weeklyData = await weeklyRes.json();
        const monthlyData = await monthlyRes.json();
        setWeeklyNews(weeklyData?.articles || []);
        setMonthlyNews(monthlyData?.articles || []);
      } catch (err) {
        console.error(err);
        setError('Failed to load news. Please check if the backend is running.');
      } finally {
        setIsNewsLoading(false); // Always set loading to false after fetch
      }
    };
    fetchNews();
      
    // 3. Load Chat History
    const savedHistory = localStorage.getItem('secChatHistory');
    if (savedHistory) setHistory(JSON.parse(savedHistory));
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);
    const matchedCompany = companies.find(c => c.name.toLowerCase() === value.toLowerCase());
    setSelectedTicker(matchedCompany ? matchedCompany.ticker : null);
    if (matchedCompany) setError('');
  };

  const handleSelectCompany = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicker) {
      setError('Please select a valid company from the list.');
      return;
    }
    router.push(`/analysis/${selectedTicker}?companyName=${encodeURIComponent(inputValue)}`);
  };

  return (
    <main className="min-h-screen p-4 sm:p-8 bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* --- Main Action Column --- */}
        <div className="lg:col-span-1 space-y-8">
          <div className="w-full p-8 bg-gray-800 rounded-2xl shadow-2xl border border-gray-700">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500">SEC Filing Analysis AI</h1>
              <p className="mt-2 text-gray-400">Select a company for deep-dive analysis.</p>
            </div>
            <form onSubmit={handleSelectCompany} className="mt-8 space-y-6">
              <input list="company-options" value={inputValue} onChange={handleInputChange} placeholder="Type to search for a company..." className="w-full px-4 py-3 text-gray-200 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"/>
              <datalist id="company-options">{companies.map(c => <option key={c.ticker} value={c.name} />)}</datalist>
              <button type="submit" className="w-full py-3 font-bold text-white bg-gradient-to-r from-purple-700 to-pink-700 rounded-lg hover:from-purple-800 hover:to-pink-800 disabled:opacity-50" disabled={isLoading || !selectedTicker}>
                Analyze Company
              </button>
            </form>
            {error && <p className="mt-2 text-sm text-center text-pink-500">{error}</p>}
          </div>

          {history.length > 0 && (
            <div className="w-full p-6 bg-gray-800 rounded-2xl shadow-2xl border border-gray-700">
              <h2 className="text-xl font-semibold text-gray-300 mb-4">Recent Chats</h2>
              <ul className="space-y-3">{history.map(chat => <li key={chat.docId}><Link href={`/chat?docId=${chat.docId}&ticker=${chat.ticker}&companyName=${encodeURIComponent(chat.companyName)}`} className="block p-4 bg-gray-700 rounded-lg hover:bg-purple-900/50 border border-gray-600"><div className="font-bold text-purple-400">{chat.companyName}</div></Link></li>)}</ul>
            </div>
          )}
        </div>

        {/* --- News Columns --- */}
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-6 bg-gray-800/50 rounded-2xl border border-gray-700">
            <h2 className="text-xl font-semibold text-gray-300 mb-4">Latest Finance News (Past Week)</h2>
            <div className="space-y-4">
              {isNewsLoading ? (
                <p>Loading news...</p>
              ) : weeklyNews.length > 0 ? (
                weeklyNews.map((article, i) => <NewsCard key={i} article={article} />)
              ) : (
                <p>No recent news found.</p>
              )}
            </div>
            {!isNewsLoading && weeklyNews.length > 0 && <Link href="/news?period=week" className="block mt-4 text-center text-purple-400 hover:text-purple-300">More News &rarr;</Link>}
          </div>
          <div className="p-6 bg-gray-800/50 rounded-2xl border border-gray-700">
            <h2 className="text-xl font-semibold text-gray-300 mb-4">Breaking News (Past Month)</h2>
            <div className="space-y-4">
              {isNewsLoading ? (
                <p>Loading news...</p>
              ) : monthlyNews.length > 0 ? (
                monthlyNews.map((article, i) => <NewsCard key={i} article={article} />)
              ) : (
                <p>No news found for the past month.</p>
              )}
            </div>
            {!isNewsLoading && monthlyNews.length > 0 && <Link href="/news?period=month" className="block mt-4 text-center text-purple-400 hover:text-purple-300">More News &rarr;</Link>}
          </div>
        </div>
      </div>
    </main>
  );
}