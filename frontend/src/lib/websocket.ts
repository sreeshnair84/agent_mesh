import { io, Socket } from 'socket.io-client'

class WebSocketClient {
  private socket: Socket | null = null

  connect(token: string) {
    this.socket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', {
      auth: { token },
    })

    this.socket.on('connect', () => {
      console.log('Connected to WebSocket')
    })

    this.socket.on('agent_status_update', (data) => {
      // Handle agent status updates
      console.log('Agent status update:', data)
    })

    this.socket.on('transaction_update', (data) => {
      // Handle transaction updates for observability
      console.log('Transaction update:', data)
    })

    this.socket.on('workflow_status_update', (data) => {
      // Handle workflow status updates
      console.log('Workflow status update:', data)
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket')
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  subscribeToAgent(agentId: string) {
    if (this.socket) {
      this.socket.emit('subscribe_agent', { agentId })
    }
  }

  subscribeToWorkflow(workflowId: string) {
    if (this.socket) {
      this.socket.emit('subscribe_workflow', { workflowId })
    }
  }

  unsubscribeFromAgent(agentId: string) {
    if (this.socket) {
      this.socket.emit('unsubscribe_agent', { agentId })
    }
  }

  unsubscribeFromWorkflow(workflowId: string) {
    if (this.socket) {
      this.socket.emit('unsubscribe_workflow', { workflowId })
    }
  }
}

export const wsClient = new WebSocketClient()
