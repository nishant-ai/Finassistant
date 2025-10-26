// Fixed Ticker Page with Working Charts
'use client';

import { Suspense, useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { startOfYear } from 'date-fns';

// --- Chart Imports ---
import { Line, Chart } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale, Filler, ChartOptions } from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale, Filler, CandlestickController, CandlestickElement);

// --- Type Definitions ---
interface KeyInfo { MarketCapitalization?: string; PERatio?: string; DividendYield?: string; Beta?: string; AnalystTargetPrice?: string; }
interface Article { title: string; description: string; url: string; }
interface OHLCData { x: string | number | Date; o: number; h: number; l: number; c: number; }
type TimeFilter = '1D' | '7D' | '1M' | 'YTD' | '1Y';
type ChartType = 'line' | 'candlestick';

// --- InfoCard Component ---
const InfoCard = ({ label, value, error }: { label: string; value: string | undefined; error?: boolean }) => {
  let displayValue = 'N/A';
  if (error) {
    displayValue = 'Loading...';
  } else if (value && value !== 'None') {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      if (label === 'Market Cap') displayValue = `$${(numValue / 1e9).toFixed(2)}B`;
      else if (label === 'Dividend Yield') displayValue = `${(numValue * 100).toFixed(2)}%`;
      else displayValue = numValue.toLocaleString();
    } else {
      displayValue = value;
    }
  }
  return (
    <div className={`p-4 bg-gray-800 rounded-lg border ${error ? 'border-yellow-500' : 'border-gray-700'}`}>
      <p className="text-sm text-gray-400">{label}</p>
      <p className={`text-xl font-bold ${error ? 'text-yellow-400' : 'text-purple-400'}`}>{displayValue}</p>
    </div>
  );
};

// --- Main Page Component ---
function AnalysisPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const ticker = params.ticker as string;
  const companyName = searchParams.get('companyName') || ticker;

  const [keyInfo, setKeyInfo] = useState<KeyInfo | null>(null);
  const [keyInfoError, setKeyInfoError] = useState(false);
  const [companyNews, setCompanyNews] = useState<Article[]>([]);
  const [isNewsLoading, setIsNewsLoading] = useState(true);
  const [chartData, setChartData] = useState<OHLCData[]>([]);
  const [activeFilter, setActiveFilter] = useState<TimeFilter>('1Y');
  const [chartType, setChartType] = useState<ChartType>('line');
  const [isSecLoading, setIsSecLoading] = useState(false);
  const [isChartLoading, setIsChartLoading] = useState(true);

  // --- Fetch KEY INFO ---
  useEffect(() => {
    if (!ticker) return;
    const fetchInfo = async () => {
      try {
        const infoRes = await fetch(`http://127.0.0.1:8000/stock/${ticker}/key-info`);
        if (!infoRes.ok) {
          if (infoRes.status === 429 || infoRes.status === 404) {
            setKeyInfoError(true);
            return;
          }
          throw new Error(`Key info fetch failed with status ${infoRes.status}`);
        }
        const data = await infoRes.json();
        setKeyInfo(data);
        setKeyInfoError(false);
      } catch (err) {
        console.error("Failed to fetch key info:", err);
        setKeyInfoError(true);
      }
    };
    fetchInfo();
  }, [ticker]);

  // --- Fetch NEWS ---
  useEffect(() => {
    if (!ticker) return;
    const fetchNews = async () => {
      setIsNewsLoading(true);
      try {
        const newsRes = await fetch(`http://127.0.0.1:8000/news/${ticker}?limit=6`);
        if (!newsRes.ok) throw new Error("News fetch failed.");
        const newsData = await newsRes.json();
        setCompanyNews(newsData?.articles || []);
      } catch (err) { 
        console.error("Failed to fetch news:", err); 
      } finally {
        setIsNewsLoading(false);
      }
    };
    fetchNews();
  }, [ticker]);

  // --- Fetch CHART DATA ---
  useEffect(() => {
    if (!ticker) return;
    const fetchChartData = async () => {
      setIsChartLoading(true);
      try {
        let url = '';
        if (activeFilter === '1D' || activeFilter === '7D') {
          url = `http://127.0.0.1:8000/stock/${ticker}/intraday-data`;
        } else {
          url = `http://127.0.0.1:8000/stock/${ticker}/historical-data`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch chart data.');
        const data = await response.json();
        
        // Filter data based on time range
        let filteredData = data;
        const now = new Date();
        
        if (activeFilter === '1D') {
          const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
          filteredData = data.filter((d: OHLCData) => new Date(d.x) >= oneDayAgo);
        } else if (activeFilter === '7D') {
          const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          filteredData = data.filter((d: OHLCData) => new Date(d.x) >= sevenDaysAgo);
        } else if (activeFilter === '1M') {
          const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          filteredData = data.filter((d: OHLCData) => new Date(d.x) >= oneMonthAgo);
        } else if (activeFilter === 'YTD') {
          const yearStart = startOfYear(now);
          filteredData = data.filter((d: OHLCData) => new Date(d.x) >= yearStart);
        }
        
        setChartData(filteredData);
      } catch (err: any) {
        console.error("Failed to fetch chart data:", err);
      } finally {
        setIsChartLoading(false);
      }
    };
    fetchChartData();
  }, [ticker, activeFilter]);
  
  const handleOpenChat = async () => {
    setIsSecLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/preprocess-and-index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker })
      });
      if (!response.ok) throw new Error('Failed to process SEC filing.');
      const data = await response.json();
      const chatHistory = JSON.parse(localStorage.getItem('secChatHistory') || '[]');
      const newEntry = { docId: data.document_id, companyName, ticker };
      const updatedHistory = [newEntry, ...chatHistory.filter((item: any) => item.ticker !== ticker)].slice(0, 5);
      localStorage.setItem('secChatHistory', JSON.stringify(updatedHistory));
      router.push(`/chat?docId=${data.document_id}&ticker=${ticker}&companyName=${encodeURIComponent(companyName)}`);
    } catch (err) {
      console.error('Error processing SEC filing:', err);
      alert('Failed to load SEC filing. Please try again.');
    } finally {
      setIsSecLoading(false);
    }
  };
  
  const FilterButton = ({ filter, label }: { filter: TimeFilter; label: string }) => (
    <button 
      onClick={() => setActiveFilter(filter)} 
      className={`px-3 py-1 text-sm rounded-md transition ${
        activeFilter === filter 
          ? 'bg-purple-600 text-white' 
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
      }`}
    >
      {label}
    </button>
  );
  
  // Memoize chart options to prevent unnecessary re-renders
  const chartOptions = useMemo<ChartOptions<any>>(() => {
    let timeUnit: 'hour' | 'day' | 'week' | 'month' = 'day';
    
    if (activeFilter === '1D') timeUnit = 'hour';
    else if (activeFilter === '7D' || activeFilter === '1M') timeUnit = 'day';
    else if (activeFilter === 'YTD') timeUnit = 'week';
    else if (activeFilter === '1Y') timeUnit = 'month';

    return {
      maintainAspectRatio: false,
      responsive: true,
      interaction: { intersect: false, mode: 'index' },
      scales: { 
        x: { 
          type: 'time',
          time: { unit: timeUnit },
          ticks: { color: '#9ca3af' },
          grid: { color: 'rgba(156, 163, 175, 0.1)' }
        }, 
        y: { 
          ticks: { 
            callback: (value) => `$${value}`,
            color: '#9ca3af'
          },
          grid: { color: 'rgba(156, 163, 175, 0.1)' }
        } 
      },
      plugins: { 
        legend: { display: false }, 
        tooltip: { 
          callbacks: { 
            label: (context) => {
              if (chartType === 'candlestick') {
                const raw = context.raw as any;
                return [
                  `Open: $${raw.o?.toFixed(2)}`,
                  `High: $${raw.h?.toFixed(2)}`,
                  `Low: $${raw.l?.toFixed(2)}`,
                  `Close: $${raw.c?.toFixed(2)}`
                ];
              }
              return `Price: $${context.parsed.y?.toFixed(2)}`;
            }
          } 
        } 
      }
    };
  }, [activeFilter, chartType]);

  // Memoize chart data to prevent unnecessary re-renders
  const preparedChartData = useMemo(() => {
    if (chartType === 'candlestick') {
      return {
        datasets: [{
          label: `${ticker} Price`,
          data: chartData.map(d => ({
            x: new Date(d.x).getTime(),
            o: d.o,
            h: d.h,
            l: d.l,
            c: d.c
          })),
          borderColor: '#a855f7',
          color: {
            up: 'rgba(34, 197, 94, 0.8)',
            down: 'rgba(239, 68, 68, 0.8)',
            unchanged: 'rgba(156, 163, 175, 0.8)'
          }
        }]
      };
    } else {
      return {
        datasets: [{
          label: `${ticker} Price`,
          data: chartData.map(d => ({ 
            x: new Date(d.x).getTime(), 
            y: d.c 
          })),
          borderColor: '#a855f7',
          backgroundColor: 'rgba(168, 85, 247, 0.2)',
          fill: true,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 4,
        }]
      };
    }
  }, [chartData, chartType, ticker]);

  return (
    <main className="min-h-screen p-4 sm:p-8 bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <Link href="/" className="flex items-center gap-2 text-sm text-purple-400 hover:text-purple-300 mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                <path fillRule="evenodd" d="M17 10a.75.75 0 0 1-.75.75H5.612l4.158 3.96a.75.75 0 1 1-1.04 1.08l-5.5-5.25a.75.75 0 0 1 0-1.08l5.5-5.25a.75.75 0 1 1 1.04 1.08L5.612 9.25H16.25A.75.75 0 0 1 17 10Z" clipRule="evenodd" />
              </svg>
              Back to Home
            </Link>
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500">
              {companyName}
            </h1>
            <p className="text-gray-400">Ticker: {ticker.toUpperCase()}</p>
          </div>
          <button 
            onClick={handleOpenChat} 
            className="px-5 py-2.5 font-bold text-white bg-gradient-to-r from-purple-700 to-pink-700 rounded-lg hover:from-purple-800 hover:to-pink-800 disabled:opacity-50 whitespace-nowrap" 
            disabled={isSecLoading}
          >
            {isSecLoading ? 'Loading Filing...' : 'Chat with SEC Filing'}
          </button>
        </div>
        
        {/* Chart and Key Info Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Chart Section */}
          <div className="lg:col-span-2 p-6 bg-gray-800 rounded-2xl border border-gray-700">
            <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
              <div className="flex space-x-2">
                <button 
                  onClick={() => setChartType('line')} 
                  className={`px-3 py-1 text-sm rounded-md transition ${
                    chartType === 'line' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Line
                </button>
                <button 
                  onClick={() => setChartType('candlestick')} 
                  className={`px-3 py-1 text-sm rounded-md transition ${
                    chartType === 'candlestick' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Candlestick
                </button>
              </div>
              <div className="flex space-x-2">
                <FilterButton filter="1D" label="1D"/>
                <FilterButton filter="7D" label="7D"/>
                <FilterButton filter="1M" label="1M"/>
                <FilterButton filter="YTD" label="YTD" />
                <FilterButton filter="1Y" label="1Y"/>
              </div>
            </div>
            <div className="h-[400px]">
              {isChartLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-purple-500 border-r-transparent"></div>
                    <p className="mt-2 text-gray-400">Loading chart data...</p>
                  </div>
                </div>
              ) : chartData.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-400">No chart data available for this period.</p>
                </div>
              ) : (
                <Chart 
                  type={chartType} 
                  data={preparedChartData} 
                  options={chartOptions} 
                />
              )}
            </div>
          </div>
          
          {/* Key Info Cards */}
          <div className="space-y-4">
            <InfoCard label="Market Cap" value={keyInfo?.MarketCapitalization} error={keyInfoError}/>
            <InfoCard label="P/E Ratio" value={keyInfo?.PERatio} error={keyInfoError}/>
            <InfoCard label="Dividend Yield" value={keyInfo?.DividendYield} error={keyInfoError}/>
            <InfoCard label="Beta" value={keyInfo?.Beta} error={keyInfoError}/>
            <InfoCard label="Analyst Target Price" value={keyInfo?.AnalystTargetPrice} error={keyInfoError}/>
          </div>
        </div>
        
        {/* News Section */}
        <div className="mt-8 p-6 bg-gray-800/50 rounded-2xl border border-gray-700">
          <h2 className="text-2xl font-semibold text-gray-300 mb-4">Related News</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {isNewsLoading ? (
              <div className="col-span-full text-center py-8">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-purple-500 border-r-transparent"></div>
                <p className="mt-2 text-gray-400">Loading news...</p>
              </div>
            ) : companyNews.length > 0 ? (
              companyNews.map((article, i) => (
                <a 
                  key={i} 
                  href={article.url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="block p-4 bg-gray-700 rounded-lg hover:bg-purple-900/50 border border-gray-700 transition"
                >
                  <h3 className="font-bold text-purple-400 line-clamp-2">{article.title}</h3>
                  <p className="text-sm text-gray-400 mt-1 line-clamp-3">{article.description}</p>
                </a>
              ))
            ) : (
              <p className="col-span-full text-center text-gray-400 py-8">
                No recent news found for this company.
              </p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default function AnalysisPageWrapper() {
  return <Suspense><AnalysisPage/></Suspense>;
}