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
        this.connect();
        setInterval(() => {
            if (!this.connected) {
                this.connect();
            }
        }, 5000);
    }

    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8766');

            this.ws.onopen = () => {
                console.log('已连接到服务器');
                this.connected = true;
                this.requestStatus();
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
            case 'config':
                this.loadConfig(data.data);
                break;
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

        list.innerHTML = positions.map(p => {
            const pnl = p.pnl || 0;
            const pnlClass = pnl >= 0 ? 'positive' : 'negative';
            return `
                <div class="position-item ${p.direction.toLowerCase()}">
                    <span>${p.direction} @ ${p.buy_price.toFixed(2)}</span>
                    <span class="pnl ${pnlClass}">${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}</span>
                </div>
            `;
        }).join('');
    }

    addTrade(trade) {
        this.trades.unshift(trade);
        this.renderTrades();
    }

    renderTrades() {
        const list = document.getElementById('trades-list');

        if (this.trades.length === 0) {
            list.innerHTML = '<p>暂无交易</p>';
            return;
        }

        list.innerHTML = this.trades.map(t => {
            const sideClass = t.side.toLowerCase();
            return `
                <div class="trade-item">
                    <div class="header">
                        <span class="side ${sideClass}">${t.side} ${t.direction}</span>
                        <span>${new Date(t.timestamp * 1000).toLocaleTimeString()}</span>
                    </div>
                    <div>价格: ${t.price.toFixed(2)} | 数量: $${t.amount}</div>
                    ${t.exit_reason ? `<div class="exit-reason">退出: ${t.exit_reason} | 盈亏: ${(t.pnl || 0).toFixed(2)}</div>` : ''}
                </div>
            `;
        }).join('');
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

    send(data) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new TradingApp();
});
