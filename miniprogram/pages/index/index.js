// 简报 H5 地址：改成你的实际部署地址（GitHub Pages / CloudStudio / 自有域名）
const H5_URL = "https://github.com/sunke1980/ai-hot-briefing/";

Page({
  data: {
    url: H5_URL
  },

  // 分享到朋友圈（小程序卡片形式，内含 H5 简报）
  onShareTimeline() {
    return {
      title: "AI HOT 每日简报 · 今天 AI 圈最值得看的 10 件事",
      query: "",
      // 可选：填一个 https 图片地址作为朋友圈封面；留空则用小程序默认图
      imageUrl: ""
    };
  },

  // 分享给微信好友
  onShareAppMessage() {
    return {
      title: "AI HOT 每日简报",
      path: "/pages/index/index"
    };
  }
});
