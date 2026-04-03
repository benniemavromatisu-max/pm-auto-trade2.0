class TradingApp {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.state = 'IDLE';
        this.prices = { YES: 0, NO: 0 };
        this.positions = [];
        this.trades = [];

        this.initTabs();
        this.initWebSocket();
        this.initControls();
        this.initConfigForm();
    }

    initTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
            });
        });
    }

    initWebSocket() {
        this._reconnectDelay = 1000;  // Initial reconnect delay (ms)
        this._maxReconnectDelay = 30000;  // Max delay (30s)
        this._connect();
        setInterval(() => {
            if (!this.connected) {
                this._connect();
            }
        }, this._reconnectDelay);
    }

    _connect() {
        if (this._connecting) return;
        this._connecting = true;

        try {
            this.ws = new WebSocket('ws://localhost:8766');

            this.ws.onopen = () => {
                console.log('已连接到服务器');
                this.connected = true;
                this._connecting = false;
                this._reconnectDelay = 1000;  // Reset delay on success
                this.requestStatus();
                this.requestTrades();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('已断开服务器连接');
                this.connected = false;
                this._connecting = false;
                this._scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.connected = false;
                this._connecting = false;
            };
        } catch (error) {
            console.error('Connection failed:', error);
            this._connecting = false;
            this._scheduleReconnect();
        }
    }

    _scheduleReconnect() {
        // Exponential backoff with jitter
        const delay = Math.min(
            this._reconnectDelay + Math.random() * 1000,
            this._maxReconnectDelay
        );
        this._reconnectDelay = Math.min(this._reconnectDelay * 2, this._maxReconnectDelay);
        setTimeout(() => {
            if (!this.connected) {
                this._connect();
            }
        }, delay);
    }

    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8766');

            this.ws.onopen = () => {
                console.log('已连接到服务器');
                this.connected = true;
                this.requestStatus();
                this.requestTrades();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('已断开服务器连接');
                this.connected = false;
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.connected = false;
            };
        } catch (error) {
            console.error('Connection failed:', error);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'status':
                this.updateStatus(data.data);
                break;
            case 'market_update':
                this.updateMarket(data.data);
                break;
            case 'trade_update':
                this.addTrade(data.data);
                break;
            case 'trades':
                this.trades = data.data || [];
                this.renderTrades();
                break;
            case 'config':
                this.loadConfig(data.data);
                break;
            case 'error':
                this.showError(data.message);
                break;
        }
    }

    showError(message) {
        console.error('交易错误:', message);
        const toast = document.getElementById('error-toast');
        const msgEl = document.getElementById('error-message');
        if (toast && msgEl) {
            msgEl.textContent = '交易错误: ' + message;
            toast.classList.remove('hidden');
            // 5秒后自动隐藏
            clearTimeout(this._errorTimeout);
            this._errorTimeout = setTimeout(() => {
                toast.classList.add('hidden');
            }, 5000);
        }
    }

    updateStatus(status) {
        this.state = status.state;
        document.getElementById('status').textContent = status.state;
        document.getElementById('market-slug').textContent = status.slug || '加载中...';

        if (status.yes_price) {
            this.prices.YES = status.yes_price;
            document.getElementById('yes-price').textContent = status.yes_price.toFixed(2);
        }

        if (status.no_price) {
            this.prices.NO = status.no_price;
            document.getElementById('no-price').textContent = status.no_price.toFixed(2);
        }

        this.updatePositions(status.positions || []);
    }

    updateMarket(data) {
        if (data.slug) {
            document.getElementById('market-slug').textContent = data.slug;
        }

        if (data.yes_price) {
            this.prices.YES = data.yes_price;
            document.getElementById('yes-price').textContent = data.yes_price.toFixed(2);
        }

        if (data.no_price) {
            this.prices.NO = data.no_price;
            document.getElementById('no-price').textContent = data.no_price.toFixed(2);
        }

        if (data.time_until_start !== undefined) {
            document.getElementById('time-start').textContent = Math.max(0, data.time_until_start).toFixed(0);
        }

        if (data.time_until_end !== undefined) {
            document.getElementById('time-end').textContent = Math.max(0, data.time_until_end).toFixed(0);
        }

        if (data.state) {
            this.state = data.state;
            document.getElementById('status').textContent = data.state;
        }
    }

    updatePositions(positions) {
        this.positions = positions;
        const list = document.getElementById('positions-list');

        if (positions.length === 0) {
            list.innerHTML = '<p>暂无持仓</p>';
            return;
        }

        // Use textContent for user data to prevent XSS
        list.innerHTML = '';
        positions.forEach(p => {
            const pnl = p.pnl || 0;
            const pnlClass = pnl >= 0 ? 'positive' : 'negative';

            const item = document.createElement('div');
            item.className = `position-item ${String(p.direction).toLowerCase()}`;

            const directionSpan = document.createElement('span');
            directionSpan.textContent = `${p.direction} @ ${p.buy_price.toFixed(2)}`;

            const pnlSpan = document.createElement('span');
            pnlSpan.className = `pnl ${pnlClass}`;
            pnlSpan.textContent = `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}`;

            item.appendChild(directionSpan);
            item.appendChild(pnlSpan);
            list.appendChild(item);
        });
    }

    addTrade(trade) {
        this.trades.unshift(trade);
        // Bound trades array to prevent memory leak
        const MAX_TRADES = 100;
        if (this.trades.length > MAX_TRADES) {
            this.trades = this.trades.slice(0, MAX_TRADES);
        }
        this.renderTrades();
    }

    renderTrades() {
        const list = document.getElementById('trades-list');

        if (this.trades.length === 0) {
            list.innerHTML = '<p>暂无交易</p>';
            return;
        }

        // Use textContent for user data to prevent XSS
        list.innerHTML = '';
        this.trades.forEach(t => {
            const item = document.createElement('div');
            item.className = 'trade-item';

            const header = document.createElement('div');
            header.className = 'header';

            const sideSpan = document.createElement('span');
            sideSpan.className = `side ${String(t.side).toLowerCase()}`;
            sideSpan.textContent = `${t.side} ${t.direction}`;

            const timeSpan = document.createElement('span');
            timeSpan.textContent = new Date(t.timestamp * 1000).toLocaleTimeString();

            header.appendChild(sideSpan);
            header.appendChild(timeSpan);

            const priceDiv = document.createElement('div');
            priceDiv.textContent = `价格: ${t.price.toFixed(2)} | 数量: $${t.amount}`;

            item.appendChild(header);
            item.appendChild(priceDiv);

            if (t.timing) {
                const timingDiv = document.createElement('div');
                timingDiv.className = 'timing-info';
                timingDiv.style.color = '#888';
                timingDiv.style.fontSize = '11px';
                if (t.side === 'BUY') {
                    timingDiv.textContent = `耗时: 检测到下单${t.timing.detect_to_order}s, 请求${t.timing.order_request}s`;
                } else {
                    timingDiv.textContent = `耗时: 检测到卖出${t.timing.detect_to_sell}s, 请求${t.timing.sell_request}s`;
                }
                item.appendChild(timingDiv);
            }

            if (t.exit_reason) {
                const exitDiv = document.createElement('div');
                exitDiv.className = 'exit-reason';
                exitDiv.textContent = `退出: ${t.exit_reason} | 盈亏: ${(t.pnl || 0).toFixed(2)}`;
                item.appendChild(exitDiv);
            }

            list.appendChild(item);
        });
    }

    loadConfig(config) {
        if (config.strategy) {
            Object.entries(config.strategy).forEach(([key, value]) => {
                const input = document.getElementById(key);
                if (input) input.value = value;
            });
        }
    }

    initControls() {
        document.getElementById('btn-start').addEventListener('click', () => {
            this.send({ type: 'start' });
        });

        document.getElementById('btn-stop').addEventListener('click', () => {
            this.send({ type: 'stop' });
        });

        document.getElementById('error-close').addEventListener('click', () => {
            document.getElementById('error-toast').classList.add('hidden');
        });
    }

    initConfigForm() {
        document.getElementById('config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const strategy = {};
            ['buy_price_min', 'buy_price_max', 'stop_loss', 'take_profit',
             'slippage', 'buy_window_minutes', 'force_close_minutes',
             'rounds_per_market', 'buy_amount'].forEach(key => {
                const input = document.getElementById(key);
                if (input) {
                    strategy[key] = parseFloat(input.value);
                }
            });
            this.send({ type: 'update_config', data: { strategy } });
        });
    }

    requestStatus() {
        this.send({ type: 'get_status' });
    }

    requestTrades() {
        this.send({ type: 'get_trades' });
    }

    send(data) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new TradingApp();
});
