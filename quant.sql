/*
 Navicat Premium Dump SQL

 Source Server         : 本地量化
 Source Server Type    : MySQL
 Source Server Version : 90400 (9.4.0)
 Source Host           : localhost:3306
 Source Schema         : quant

 Target Server Type    : MySQL
 Target Server Version : 90400 (9.4.0)
 File Encoding         : 65001

 Date: 11/08/2025 19:19:57
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for closures
-- ----------------------------
DROP TABLE IF EXISTS `closures`;
CREATE TABLE `closures`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `strategy_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '策略ID',
  `trade_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '原始订单 ID',
  `reason` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '止盈/止损',
  `close_price` float NOT NULL COMMENT '平仓价格',
  `pnl` float NOT NULL COMMENT '盈亏百分比',
  `close_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '平仓时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3416 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of closures
-- ----------------------------

-- ----------------------------
-- Table structure for logs
-- ----------------------------
DROP TABLE IF EXISTS `logs`;
CREATE TABLE `logs`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `strategy_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `time` datetime NULL DEFAULT NULL,
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5313 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of logs
-- ----------------------------

-- ----------------------------
-- Table structure for strategies
-- ----------------------------
DROP TABLE IF EXISTS `strategies`;
CREATE TABLE `strategies`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `strategy_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `symbol` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `interval` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `leverage` int NOT NULL DEFAULT 125,
  `position_size` int NOT NULL,
  `take_profit_percent` float NOT NULL,
  `stop_loss_percent` float NOT NULL,
  `rsi_period` int NOT NULL,
  `rsi_acc_period` int NOT NULL,
  `rsi_long_threshold` float NOT NULL,
  `rsi_short_threshold` float NOT NULL,
  `max_positions` int NULL DEFAULT NULL,
  `running` tinyint(1) NOT NULL DEFAULT 0,
  `updated_at` datetime NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `strategy_id`(`strategy_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of strategies
-- ----------------------------
INSERT INTO `strategies` VALUES (1, 'BTC_RSI_1m', 'BTC_USDT', '1m', 125, 1, 80, 400, 2, 5, 20, 80, 1000, 1, '2025-08-11 19:15:26', '2025-08-02 20:36:07');

-- ----------------------------
-- Table structure for tp_sl_orders
-- ----------------------------
DROP TABLE IF EXISTS `tp_sl_orders`;
CREATE TABLE `tp_sl_orders`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `strategy_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `trade_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `symbol` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `order_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `price` float NULL DEFAULT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'open',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `signal` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `open_price` float NULL DEFAULT NULL,
  `size` float NULL DEFAULT NULL,
  `pair_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8975 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of tp_sl_orders
-- ----------------------------

-- ----------------------------
-- Table structure for trades
-- ----------------------------
DROP TABLE IF EXISTS `trades`;
CREATE TABLE `trades`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '交易记录主键，自增ID',
  `strategy_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '策略ID，用于区分不同的策略实例',
  `symbol` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '交易币种/合约，例如 BTC_USDT',
  `signal` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '交易信号，long 表示做多，short 表示做空',
  `size` int NULL DEFAULT NULL COMMENT '开仓数量，单位与平台一致',
  `leverage` int NULL DEFAULT NULL COMMENT '杠杆倍数',
  `take_profit_percent` float NULL DEFAULT NULL COMMENT '止盈百分比，如80表示盈利80%时止盈',
  `stop_loss_percent` float NULL DEFAULT NULL COMMENT '止损百分比，如400表示亏损400%时止损',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '订单状态，如 open（持仓中）、closed（已平仓）',
  `trade_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '开仓订单的唯一ID（平台返回）',
  `open_price` float NULL DEFAULT NULL COMMENT '开仓价格',
  `close_price` float NULL DEFAULT NULL COMMENT '平仓价格',
  `pnl` float NULL DEFAULT NULL COMMENT '本次交易盈亏金额（已考虑杠杆）',
  `open_time` datetime NULL DEFAULT NULL COMMENT '开仓时间',
  `close_time` datetime NULL DEFAULT NULL COMMENT '平仓时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4834 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of trades
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
