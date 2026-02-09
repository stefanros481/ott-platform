import { useNavigate, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getFeatured } from '../api/catalog'
import { getHomeRecommendations } from '../api/recommendations'
import HeroBanner from '../components/HeroBanner'
import ContentRail from '../components/ContentRail'
import TitleCard from '../components/TitleCard'

export default function HomePage() {
  const { profile } = useAuth()
  const navigate = useNavigate()

  const { data: featured, isLoading: featuredLoading } = useQuery({
    queryKey: ['featured'],
    queryFn: getFeatured,
    enabled: !!profile,
  })

  const { data: recommendations, isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations', 'home', profile?.id],
    queryFn: () => getHomeRecommendations(profile!.id),
    enabled: !!profile,
  })

  if (!profile) {
    return <Navigate to="/profiles" replace />
  }

  const heroItems = (featured || []).slice(0, 5).map(t => ({
    id: t.id,
    title: t.title,
    synopsis: t.synopsis_short || '',
    landscapeUrl: t.landscape_url,
    posterUrl: t.poster_url,
  }))

  const isRecent = (dateStr: string) => {
    const created = new Date(dateStr)
    const daysAgo = (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24)
    return daysAgo <= 30
  }

  return (
    <div className="pb-12">
      {/* Hero Banner */}
      {featuredLoading ? (
        <div className="w-full h-[50vh] sm:h-[60vh] lg:h-[70vh] bg-surface-raised animate-pulse" />
      ) : (
        <HeroBanner
          items={heroItems}
          onPlay={id => navigate(`/play/movie/${id}`)}
          onMoreInfo={id => navigate(`/title/${id}`)}
        />
      )}

      {/* Content Rails */}
      <div className="mt-8 space-y-10">
        {recsLoading ? (
          // Loading skeletons
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="px-4 sm:px-6 lg:px-8">
              <div className="h-6 w-48 bg-surface-overlay rounded animate-pulse mb-4" />
              <div className="flex gap-3 overflow-hidden">
                {Array.from({ length: 6 }).map((_, j) => (
                  <div key={j} className="flex-shrink-0 w-[160px] sm:w-[180px] md:w-[200px]">
                    <div className="aspect-[2/3] rounded-lg bg-surface-overlay animate-pulse" />
                    <div className="h-4 w-24 bg-surface-overlay rounded animate-pulse mt-2" />
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          recommendations?.rails.map(rail => (
            <ContentRail key={rail.name} title={rail.name}>
              {rail.items.map(item => (
                <TitleCard
                  key={item.id}
                  title={item.title}
                  posterUrl={item.poster_url}
                  landscapeUrl={item.landscape_url}
                  titleType={item.title_type}
                  releaseYear={item.release_year}
                  ageRating={item.age_rating}
                  onClick={() => navigate(`/title/${item.id}`)}
                  isNew={isRecent(String(item.release_year))}
                />
              ))}
            </ContentRail>
          ))
        )}
      </div>
    </div>
  )
}
