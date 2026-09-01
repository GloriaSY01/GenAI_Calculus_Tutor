import { useLang } from '../../i18n.jsx'
import { Card, Badge, Empty } from '../../components/ui.jsx'

export default function Favorites({ favorites, onRemove, onPractice, onBack }) {
  const { t } = useLang()
  const diffLabel = (d) => t('diff_' + d)
  const qtypeLabel = (x) => t('qtype_' + x)

  return (
    <div className="stack fade-in">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="section-step">{t('stu_favorites')}</div>
          <h2 className="section-head">{t('fav_heading')}</h2>
        </div>
        <button className="btn" onClick={onBack}>{t('stu_back_learning')}</button>
      </div>

      {favorites.length === 0 ? (
        <Card><Empty icon="⭐">{t('fav_empty')}</Empty></Card>
      ) : (
        <div className="stack" style={{ gap: 12 }}>
          {favorites.map((f) => (
            <Card key={f.question_id}>
              <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div className="row" style={{ gap: 8, marginBottom: 8 }}>
                    <Badge level="neutral">{f.topic}</Badge>
                    <Badge level="neutral">{diffLabel(f.difficulty)}</Badge>
                    <Badge level="neutral">{qtypeLabel(f.type)}</Badge>
                  </div>
                  <div style={{ lineHeight: 1.6 }}>{f.stem}</div>
                </div>
                <div className="stack" style={{ gap: 6 }}>
                  <button className="btn sm primary" onClick={() => onPractice(f)}>{t('fav_practice_this')}</button>
                  <button className="btn sm ghost" onClick={() => onRemove(f.question_id)}>{t('fav_remove')}</button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
