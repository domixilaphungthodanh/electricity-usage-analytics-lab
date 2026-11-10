import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .analysis import compare
from .db import ROOT, DEFAULT_DB
from .sample import START, END


def export(db=DEFAULT_DB, start=START, end=END, out=None):
    tables = compare(db, start, end)
    out = Path(out or ROOT / 'outputs')
    out.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(out / f'{name}.csv', index=False, encoding='utf-8-sig')

    sns.set_theme(style='whitegrid')
    daily = tables['daily']
    rooms = tables['room_comparison']
    common_days = int(rooms.common_days.iloc[0])
    colors = dict(zip(rooms.room, sns.color_palette(n_colors=len(rooms))))

    def save(fig, name):
        fig.text(.02, .015, f'Dữ liệu giả lập | {start} đến {end} | Giờ Việt Nam', fontsize=9)
        fig.tight_layout(rect=(0,.05,1,1))
        fig.savefig(out / name, dpi=140)
        plt.close(fig)

    def empty(ax, message):
        ax.text(.5,.5,message,transform=ax.transAxes,ha='center',va='center')
        ax.set_axis_off()

    fig, ax = plt.subplots(figsize=(11,5))
    if daily.full_day_wh.isna().all():
        empty(ax,'Kỳ này chưa có ngày đủ 24 số đo ở bất kỳ phòng nào')
    else:
        for room, frame in daily.groupby('room'):
            ax.plot(pd.to_datetime(frame.day), frame.full_day_wh.astype(float)/1000,
                    marker='o', markersize=3, color=colors[room], label=room)
        ax.set(title='Điện năng theo ngày đủ số đo', ylabel='kWh/ngày', xlabel='Ngày')
        ax.tick_params(axis='x',rotation=30)
        ax.legend()
    save(fig,'01_daily_usage.png')

    fig, ax = plt.subplots(figsize=(9,5))
    if common_days == 0:
        empty(ax,'Kỳ này chưa có ngày đủ số đo ở cả ba phòng')
    else:
        view = rooms.assign(kwh=rooms.total_wh/1000)
        sns.barplot(data=view,x='room',y='kwh',hue='room',palette=colors,legend=False,ax=ax)
        ax.set(title=f'Điện năng trên cùng {common_days} ngày đủ số đo',ylabel='kWh',xlabel='')
        for container in ax.containers:
            ax.bar_label(container,fmt='%.2f',padding=3)
        ax.margins(y=.15)
    save(fig,'02_common_days.png')

    fig, axes = plt.subplots(3,1,figsize=(12,10),sharex=True)
    summary = tables['weekday_hour']
    vmax = max(1, float(summary.mean_wh.max())) / 1000
    for (room, frame), ax in zip(summary.groupby('room',sort=False), axes):
        grid = frame.pivot(index='weekday',columns='hour',values='mean_wh').astype(float)/1000
        if grid.isna().all().all():
            empty(ax,f'{room} chưa có số đo trong kỳ')
            continue
        sns.heatmap(grid,vmin=0,vmax=vmax,cmap='YlGnBu',ax=ax,
                    cbar_kws={'label':'kWh trung bình mỗi giờ'})
        ax.set(title=room,ylabel='',xlabel='Giờ bắt đầu')
        ax.set_yticklabels(['T2','T3','T4','T5','T6','T7','CN'],rotation=0)
    save(fig,'03_weekday_hour.png')

    fig, ax = plt.subplots(figsize=(13,5))
    coverage = daily.assign(label=pd.to_datetime(daily.day).dt.strftime('%d/%m'))
    sns.barplot(data=coverage,x='label',y='coverage_pct',hue='room',palette=colors,ax=ax)
    ax.set(title='Độ bao phủ theo phòng và ngày',xlabel='Ngày',ylabel='Giờ có số đo (%)',ylim=(0,108))
    ax.tick_params(axis='x',rotation=45)
    ax.legend(title='')
    save(fig,'04_coverage.png')

    measured = int(daily.measured_hours.sum())
    expected = int(daily.expected_hours.sum())
    if common_days:
        maximum = int(rooms.total_wh.max())
        names = ', '.join(rooms.loc[rooms.total_wh.eq(maximum),'room'])
        comparison = f'{names} ghi nhận nhiều nhất trên {common_days} ngày chung đủ dữ liệu, {maximum/1000:.3f} kWh.'
    else:
        comparison = 'Có 0 ngày chung đủ dữ liệu để so sánh tổng giữa ba phòng.'
    peaks = tables['whole_house_hours']
    if peaks.empty:
        peak = 'Có 0 giờ đủ ba số đo để xác định mức tiêu thụ cao nhất toàn nhà.'
    else:
        first = peaks.iloc[0]
        ties = int(peaks.peak_rank.eq(1).sum())
        peak = (f'Trong {len(peaks)} giờ có đủ ba số đo, mức cao nhất là {first.total_wh/1000:.3f} kWh. '
                f'Có {ties} giờ cùng mức này. Mốc sớm nhất là {first.hour_start}.')
    report = [
        '# Báo cáo điện năng giả lập',
        f'Kỳ {start} đến {end}, giờ Việt Nam. Mỗi số đo là Wh của một giờ. Hình dùng kWh.',
        f'1. Ghi nhận {measured}/{expected} ô phòng–giờ, đạt {measured/expected*100:.1f}% độ bao phủ.',
        f'2. {comparison}',
        f'3. {peak}',
        'Các ngày thiếu giờ hiển thị tổng đã ghi nhận riêng. Tổng ngày và hạng ngày chỉ tính khi đủ 24 giờ. '
        'Bảng thứ–giờ kèm số mẫu và số giờ dự kiến để đọc các ô trung bình.',
    ]
    (out/'report.md').write_text('\n\n'.join(report)+'\n',encoding='utf-8')
    print(f'Đã đối chiếu SQL và pandas, xuất 4 PNG, 6 CSV và báo cáo tại {out}')
    return tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db',default=str(DEFAULT_DB))
    parser.add_argument('--start',default=START)
    parser.add_argument('--end',default=END)
    parser.add_argument('--out')
    args = parser.parse_args()
    export(args.db,args.start,args.end,args.out)


if __name__ == '__main__':
    main()
