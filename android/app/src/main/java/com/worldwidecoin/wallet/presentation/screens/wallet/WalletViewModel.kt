package com.worldwidecoin.wallet.presentation.screens.wallet

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.worldwidecoin.wallet.domain.model.Transaction
import com.worldwidecoin.wallet.domain.usecase.CreateWalletUseCase
import com.worldwidecoin.wallet.domain.usecase.GetBalanceUseCase
import com.worldwidecoin.wallet.domain.usecase.GetTransactionsUseCase
import com.worldwidecoin.wallet.domain.usecase.RefreshBalanceUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class WalletViewModel @Inject constructor(
    private val createWalletUseCase: CreateWalletUseCase,
    private val getBalanceUseCase: GetBalanceUseCase,
    private val getTransactionsUseCase: GetTransactionsUseCase,
    private val refreshBalanceUseCase: RefreshBalanceUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(WalletUiState())
    val uiState: StateFlow<WalletUiState> = _uiState.asStateFlow()

    init {
        loadWalletData()
    }

    private fun loadWalletData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            
            try {
                // Check if wallet exists
                val hasWallet = false // TODO: Check if wallet exists
                
                if (hasWallet) {
                    loadWalletContent()
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isNewWallet = true
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }

    private fun loadWalletContent() {
        viewModelScope.launch {
            try {
                val balance = getBalanceUseCase()
                val transactions = getTransactionsUseCase()
                
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    balance = balance,
                    transactions = transactions,
                    isNewWallet = false
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }

    fun createNewWallet() {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                createWalletUseCase()
                loadWalletContent()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }

    fun refreshBalance() {
        viewModelScope.launch {
            try {
                val newBalance = refreshBalanceUseCase()
                _uiState.value = _uiState.value.copy(balance = newBalance)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = e.message)
            }
        }
    }
}

data class WalletUiState(
    val isLoading: Boolean = false,
    val balance: Double = 0.0,
    val transactions: List<Transaction> = emptyList(),
    val isNewWallet: Boolean = false,
    val error: String? = null
)
