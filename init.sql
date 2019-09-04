SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pixiv_rss`
--

-- --------------------------------------------------------

--
-- 表的结构 `award_log`
--

CREATE TABLE `award_log` (
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上榜时间',
  `type` tinyint(4) NOT NULL,
  `uid` int(11) NOT NULL COMMENT '上榜用户pixiv_id'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `pixiv_weibo_id_map`
--

CREATE TABLE `pixiv_weibo_id_map` (
  `pixiv_uid` int(8) NOT NULL,
  `weibo_uid` varchar(32) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Pixiv_id与Weibo_id的映射表';

-- --------------------------------------------------------

--
-- 表的结构 `weibo_post_history`
--

CREATE TABLE `weibo_post_history` (
  `pixiv_id` int(11) NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `pixiv_weibo_id_map`
--
ALTER TABLE `pixiv_weibo_id_map`
  ADD PRIMARY KEY (`pixiv_uid`);

--
-- Indexes for table `weibo_post_history`
--
ALTER TABLE `weibo_post_history`
  ADD PRIMARY KEY (`pixiv_id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
